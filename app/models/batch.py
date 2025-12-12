from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import UUID



class BatchStatus(str, Enum):
    """Batch job status enumeration"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class BatchDeleteItem(BaseModel):
    """Result item for a single subscription in batch deletion"""
    index: int = Field(description="Index position in the request")
    subscription_id: int = Field(description="Subscription ID that was attempted to delete")
    success: bool = Field(description="Whether the deletion was successful")
    error: Optional[str] = Field(None, description="Error message (if failed)")


class BatchDeleteRequest(BaseModel):
    """Batch subscription deletion request"""
    subscription_ids: List[int] = Field(
        description="List of subscription IDs to delete",
        min_length=1,
        max_length=100,  # Limit batch size
    )
    idempotency_key: Optional[str] = Field(None, description="Idempotency key to prevent duplicate submissions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subscription_ids": [1, 2, 3, 4, 5],
                    "idempotency_key": "batch-delete-2024-01-15"
                }
            ]
        }
    }


class BatchJobResponse(BaseModel):
    """202 Accepted response - batch job created"""
    batch_id: UUID = Field(description="Batch job ID")
    status: BatchStatus = Field(description="Current status")
    status_url: str = Field(description="Status query URL")
    total_count: int = Field(description="Total number of subscriptions")
    message: str = Field(description="Message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "pending",
                    "status_url": "/subscriptions/batch/550e8400-e29b-41d4-a716-446655440000/status",
                    "total_count": 10,
                    "message": "Batch subscription deletion job created and queued for processing"
                }
            ]
        }
    }


class BatchStatusResponse(BaseModel):
    """Batch job status query response"""
    batch_id: UUID = Field(description="Batch job ID")
    status: BatchStatus = Field(description="Current status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    total_count: int = Field(description="Total number of subscriptions")
    processed_count: int = Field(description="Number of processed subscriptions")
    success_count: int = Field(description="Number of successful subscriptions")
    failed_count: int = Field(description="Number of failed subscriptions")
    progress: float = Field(ge=0, le=100, description="Processing progress percentage")
    results: Optional[List[BatchDeleteItem]] = Field(None, description="Processing results (when completed)")
    error: Optional[str] = Field(None, description="Overall error message (if job failed)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "completed",
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-15T10:00:05Z",
                    "completed_at": "2024-01-15T10:00:05Z",
                    "total_count": 10,
                    "processed_count": 10,
                    "success_count": 8,
                    "failed_count": 2,
                    "progress": 100.0,
                    "results": [
                        {
                            "index": 0,
                            "subscription_id": 1,
                            "success": True
                        },
                        {
                            "index": 1,
                            "subscription_id": 2,
                            "success": False,
                            "error": "Subscription not found"
                        }
                    ]
                }
            ]
        }
    }

