"""
Batch subscription creation service - implements 202 Accepted asynchronous processing and status polling
"""
import uuid
import time
import threading
from typing import Dict, Optional, List
from datetime import datetime
from uuid import UUID

from app.models.batch import (
    BatchStatus,
    BatchCreateRequest,
    BatchJobResponse,
    BatchStatusResponse,
    BatchSubscriptionItem,
)
from app.models.subscription import SubscriptionCreate, SubscriptionRead
from app.services.subscription_service import SqlAlchemySubscriptionService


class BatchJob:
    """Batch job data model (in-memory storage, production should use database)"""
    def __init__(
        self,
        batch_id: UUID,
        request: BatchCreateRequest,
        subscription_service: SqlAlchemySubscriptionService,
        status: BatchStatus = BatchStatus.pending,
    ):
        self.batch_id = batch_id
        self.request = request
        self.subscription_service = subscription_service
        self.status = status
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.total_count = len(request.subscriptions)
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.results: List[BatchSubscriptionItem] = []
        self.error: Optional[str] = None


class BatchSubscriptionService:
    """Batch subscription creation service - manages batch job lifecycle"""
    
    def __init__(self):
        # In-memory storage: production should use database
        self.jobs: Dict[UUID, BatchJob] = {}
        # Idempotency check
        self.idempotency_map: Dict[str, UUID] = {}
        # Background task threads
        self._processing_threads: Dict[UUID, threading.Thread] = {}
    
    def create_batch_job(
        self,
        request: BatchCreateRequest,
        subscription_service: SqlAlchemySubscriptionService,
    ) -> BatchJob:
        """
        Create a batch subscription job
        
        Execution flow:
        1. Check idempotency key
        2. Generate batch_id
        3. Create job object (status: pending)
        4. Start background processing thread
        5. Return job object
        """
        # Step 1: Check idempotency
        if request.idempotency_key:
            existing_batch_id = self.idempotency_map.get(request.idempotency_key)
            if existing_batch_id and existing_batch_id in self.jobs:
                return self.jobs[existing_batch_id]
        
        # Step 2: Generate unique ID
        batch_id = uuid.uuid4()
        
        # Step 3: Create job object
        job = BatchJob(
            batch_id=batch_id,
            request=request,
            subscription_service=subscription_service,
            status=BatchStatus.pending,
        )
        self.jobs[batch_id] = job
        
        # Step 4: Record idempotency key
        if request.idempotency_key:
            self.idempotency_map[request.idempotency_key] = batch_id
        
        # Step 5: Start background processing thread
        self._start_processing(job)
        
        return job
    
    def get_batch_status(self, batch_id: UUID) -> Optional[BatchStatusResponse]:
        """
        Get batch job status
        
        Execution flow:
        1. Find job in storage
        2. Return None if not found
        3. Calculate progress percentage
        4. Build and return status response object
        """
        job = self.jobs.get(batch_id)
        if not job:
            return None
        
        # Calculate progress
        progress = (job.processed_count / job.total_count * 100) if job.total_count > 0 else 0.0
        
        return BatchStatusResponse(
            batch_id=job.batch_id,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            total_count=job.total_count,
            processed_count=job.processed_count,
            success_count=job.success_count,
            failed_count=job.failed_count,
            progress=progress,
            results=job.results if job.status == BatchStatus.completed else None,
            error=job.error,
        )
    
    def _start_processing(self, job: BatchJob):
        """
        Start background processing thread
        
        Execution flow:
        1. Create background thread
        2. Thread executes _process_batch method
        3. Set as daemon thread
        4. Start thread (non-blocking)
        """
        thread = threading.Thread(
            target=self._process_batch,
            args=(job,),
            daemon=True
        )
        self._processing_threads[job.batch_id] = thread
        thread.start()
    
    def _process_batch(self, job: BatchJob):
        """
        Core logic for background batch subscription creation processing
        
        Detailed execution flow:
        
        Phase 1: Update status to processing
        - Update job status to processing
        - Update updated_at timestamp
        
        Phase 2: Process subscriptions one by one
        - Iterate through each subscription in request
        - Call subscription_service.create_subscription()
        - Record success/failure results
        - Update progress and counts
        
        Phase 3: Processing complete
        - Update status to completed
        - Set completed_at timestamp
        - Save all results
        """
        try:
            # ========== Phase 1: Start processing ==========
            job.status = BatchStatus.processing
            job.updated_at = datetime.utcnow()
            
            # ========== Phase 2: Process subscriptions one by one ==========
            for index, subscription_request in enumerate(job.request.subscriptions):
                try:
                    # Create single subscription
                    created_subscription = job.subscription_service.create_subscription(
                        subscription_request
                    )
                    
                    # Verify the subscription was actually created by checking if it has an ID
                    if not created_subscription or not hasattr(created_subscription, 'id') or created_subscription.id is None:
                        raise ValueError(f"Subscription creation returned invalid result: {created_subscription}")
                    
                    # Record success
                    job.results.append(BatchSubscriptionItem(
                        index=index,
                        subscription=created_subscription,
                        success=True,
                    ))
                    job.success_count += 1
                    
                except Exception as e:
                    # Record failure with detailed error information
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    job.results.append(BatchSubscriptionItem(
                        index=index,
                        subscription=None,
                        error=error_msg,
                        success=False,
                    ))
                    job.failed_count += 1
                    # Log the error (if logger is available)
                    if hasattr(job.subscription_service, 'logger'):
                        job.subscription_service.logger.error(
                            "batch_subscription_creation_failed",
                            index=index,
                            error=error_msg,
                            user_id=getattr(subscription_request, 'user_id', 'unknown')
                        )
                
                # Update progress
                job.processed_count += 1
                job.updated_at = datetime.utcnow()
                
                # Simulate processing delay (may not be needed in production)
                time.sleep(0.1)  # 100ms interval between each subscription processing
            
            # ========== Phase 3: Processing complete ==========
            job.status = BatchStatus.completed
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            
        except Exception as e:
            # ========== Phase 3: Processing failed ==========
            job.status = BatchStatus.failed
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            job.error = str(e)


# Global service instance (singleton pattern)
batch_subscription_service = BatchSubscriptionService()

