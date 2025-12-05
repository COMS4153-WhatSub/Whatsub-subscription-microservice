from typing import Optional, List
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path, status, Response, Header

from app.models.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionRead
from app.models.common import ErrorResponse, PaginatedResponse
from app.models.batch import BatchDeleteRequest, BatchJobResponse, BatchStatusResponse
from app.services.subscription_service import SubscriptionServiceProtocol
from app.services.batch_service import batch_subscription_service


router = APIRouter()


def get_subscription_service(request: Request) -> SubscriptionServiceProtocol:
    return request.app.state.subscription_service


@router.get(
    "/",
    response_model=PaginatedResponse[SubscriptionRead],
    summary="List subscriptions",
    description="List subscriptions with filtering, sorting, and pagination",
)
async def list_subscriptions(
    # Filtering parameters
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    plan: Optional[str] = Query(None, description="Filter by plan name (partial match)"),
    account: Optional[str] = Query(None, description="Filter by account name (exact match)"),
    billing_date_from: Optional[date] = Query(None, description="Filter by billing date from (inclusive)"),
    billing_date_to: Optional[date] = Query(None, description="Filter by billing date to (inclusive)"),
    price_min: Optional[Decimal] = Query(None, description="Filter by minimum price (inclusive)"),
    price_max: Optional[Decimal] = Query(None, description="Filter by maximum price (inclusive)"),
    search: Optional[str] = Query(None, description="Search in plan name and account (partial match)"),
    # Sorting parameters
    sort_by: Optional[str] = Query(
        None,
        description="Sort by field: id, user_id, plan, account, billing_date, price, created_at",
    ),
    sort_order: Optional[str] = Query(
        "desc",
        description="Sort order: asc or desc",
        regex="^(asc|desc)$",
    ),
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    return service.list_subscriptions(
        user_id=user_id,
        plan=plan,
        account=account,
        billing_date_from=billing_date_from,
        billing_date_to=billing_date_to,
        price_min=price_min,
        price_max=price_max,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )


@router.get(
    "/due",
    response_model=List[SubscriptionRead],
    summary="Get due subscriptions",
    description="Get subscriptions that are due for billing within a specified number of days.",
)
async def get_due_subscriptions(
    days_ahead: int = Query(3, ge=0, description="Number of days ahead to check for due billing"),
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    """
    Get list of subscriptions due for billing.
    This is primarily used by internal jobs/composite service.
    Returns subscriptions with billing_date between today and (today + days_ahead).
    """
    # We need to access the concrete implementation for this specific method
    # or update the protocol. For now, we assume the service has the method.
    if not hasattr(service, "find_due_subscriptions"):
        raise HTTPException(status_code=501, detail="Service does not support finding due subscriptions")
    
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    return service.find_due_subscriptions(today, end_date)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a subscription",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"message": "Failed to create subscription", "code": 400}
                }
            },
        }
    },
)
async def create_subscription(
    payload: SubscriptionCreate,
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    try:
        subscription = service.create_subscription(payload)
        response = {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "plan": subscription.plan,
            "billing_type": subscription.billing_type.value,
            "url": subscription.url,
            "account": subscription.account,
            "billing_date": subscription.billing_date.isoformat() if subscription.billing_date else None,
            "price": str(subscription.price) if subscription.price else None,
            "created_at": subscription.created_at.isoformat(),
            "_links": {
                "self": {
                    "href": f"/subscriptions/{subscription.id}"
                },
                "update": {
                    "href": f"/subscriptions/{subscription.id}",
                    "method": "PATCH",
                    "description": "Update this subscription"
                },
                "delete": {
                    "href": f"/subscriptions/{subscription.id}",
                    "method": "DELETE",
                    "description": "Delete this subscription"
                },
                "user": {
                    "href": f"/users/{subscription.user_id}",
                    "method": "GET",
                    "description": "Get the user who owns this subscription"
                }
            }
        }
        return response
    except ValueError as e:
        # Handle validation errors (e.g., invalid user_id)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Handle database errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{subscription_id}",
    summary="Get a subscription by ID",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Subscription not found",
            "content": {
                "application/json": {
                    "example": {"message": "Subscription not found", "code": 404}
                }
            },
        }
    },
)
async def get_subscription(
    subscription_id: int,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    subscription = service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Generate ETag based on subscription content
    etag_content = f"{subscription.id}-{subscription.plan}-{subscription.price}-{subscription.billing_date}-{subscription.created_at}"
    etag = hashlib.md5(etag_content.encode()).hexdigest()
    
    # Check If-None-Match header
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)
    
    # Set ETag header
    response.headers["ETag"] = etag
    
    response_data = {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "plan": subscription.plan,
        "billing_type": subscription.billing_type.value,
        "url": subscription.url,
        "account": subscription.account,
        "billing_date": subscription.billing_date.isoformat() if subscription.billing_date else None,
        "price": str(subscription.price) if subscription.price else None,
        "created_at": subscription.created_at.isoformat(),
        "_links": {
            "self": {
                "href": f"/subscriptions/{subscription.id}"
            },
            "update": {
                "href": f"/subscriptions/{subscription.id}",
                "method": "PATCH",
                "description": "Update this subscription"
            },
            "delete": {
                "href": f"/subscriptions/{subscription.id}",
                "method": "DELETE",
                "description": "Delete this subscription"
            },
            "user": {
                "href": f"/users/{subscription.user_id}",
                "method": "GET",
                "description": "Get the user who owns this subscription"
            }
        }
    }
    return response_data


@router.patch(
    "/{subscription_id}",
    summary="Update a subscription",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Subscription not found",
            "content": {
                "application/json": {
                    "example": {"message": "Subscription not found", "code": 404}
                }
            },
        }
    },
)
async def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    subscription = service.update_subscription(subscription_id, payload)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    response = {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "plan": subscription.plan,
        "billing_type": subscription.billing_type.value,
        "url": subscription.url,
        "account": subscription.account,
        "billing_date": subscription.billing_date.isoformat() if subscription.billing_date else None,
        "price": str(subscription.price) if subscription.price else None,
        "created_at": subscription.created_at.isoformat(),
        "_links": {
            "self": {
                "href": f"/subscriptions/{subscription.id}"
            },
            "update": {
                "href": f"/subscriptions/{subscription.id}",
                "method": "PATCH",
                "description": "Update this subscription"
            },
            "delete": {
                "href": f"/subscriptions/{subscription.id}",
                "method": "DELETE",
                "description": "Delete this subscription"
            },
            "user": {
                "href": f"/users/{subscription.user_id}",
                "method": "GET",
                "description": "Get the user who owns this subscription"
            }
        }
    }
    return response


@router.post(
    "/{subscription_id}/advance-date",
    response_model=SubscriptionRead,
    summary="Advance subscription billing date",
    description="Move the billing date to the next cycle (monthly/quarterly/annually).",
    responses={
        404: {"description": "Subscription not found"},
        501: {"description": "Feature not implemented in service"}
    }
)
async def advance_subscription_date(
    subscription_id: int,
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    """
    Advance billing date logic.
    This is used after a notification is sent or payment is processed.
    """
    if not hasattr(service, "advance_billing_date"):
        raise HTTPException(status_code=501, detail="Service does not support advancing billing date")
    
    subscription = service.advance_billing_date(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a subscription",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Subscription not found",
            "content": {
                "application/json": {
                    "example": {"message": "Subscription not found", "code": 404}
                }
            },
        }
    },
)
async def delete_subscription(
    subscription_id: int,
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    success = service.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return None


@router.get(
    "/batch/{batch_id}/status",
    response_model=BatchStatusResponse,
    summary="Query batch job status",
    description="""
    Query the processing status of a batch subscription creation job.
    
    Workflow:
    1. Get batch_id from URL path
    2. Query job status from service
    3. Return 404 if job does not exist
    4. Return current status information including progress and results
    
    Clients should periodically poll this endpoint until status becomes completed or failed.
    Recommended to use exponential backoff strategy:
    - First time: query immediately
    - If processing: wait 1-2 seconds then query
    - If still processing: wait 2-4 seconds then query
    - Continue with exponential backoff, max interval 10 seconds
    """,
    responses={
        200: {
            "description": "Batch job status information",
            "content": {
                "application/json": {
                    "examples": {
                        "processing": {
                            "summary": "Processing status",
                            "value": {
                                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "processing",
                                "created_at": "2024-01-15T10:00:00Z",
                                "updated_at": "2024-01-15T10:00:02Z",
                                "total_count": 10,
                                "processed_count": 5,
                                "success_count": 4,
                                "failed_count": 1,
                                "progress": 50.0
                            }
                        },
                        "completed": {
                            "summary": "Completed status",
                            "value": {
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
                                    {"index": 0, "success": True, "subscription": {...}},
                                    {"index": 1, "success": False, "error": "..."}
                                ]
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Batch job not found"
        }
    }
)
async def get_batch_status(
    batch_id: UUID = Path(..., description="Batch job ID")
) -> BatchStatusResponse:
    """
    Query batch job status endpoint
    
    Execution path:
    1. Get batch_id from path parameter
    2. Call batch_service.get_batch_status() to query status
    3. Return 404 if job does not exist
    4. Return status information (200 OK) including progress and detailed results
    
    This endpoint can be called multiple times by clients (polling),
    until the job is complete (status is completed or failed).
    """
    # Step 1-2: Query job status
    status_response = batch_subscription_service.get_batch_status(batch_id)
    
    # Step 3: Check if job exists
    if not status_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {batch_id} not found"
        )
    
    # Step 4: Return status information
    return status_response


@router.post(
    "/batch/delete",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete subscriptions in batch (asynchronous)",
    description="""
    Delete multiple subscriptions and immediately return 202 Accepted response.
    
    Workflow:
    1. Receive batch subscription deletion request
    2. Create batch job record (status: pending)
    3. Start background processing thread
    4. Immediately return 202 Accepted with batch_id and status_url
    
    Clients should use the returned status_url to poll job status until status becomes completed or failed.
    Batch operations may take longer, especially when processing large numbers of subscriptions.
    """,
    responses={
        202: {
            "description": "Batch job created and processing",
            "content": {
                "application/json": {
                    "example": {
                        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "pending",
                        "status_url": "/subscriptions/batch/550e8400-e29b-41d4-a716-446655440000/status",
                        "total_count": 10,
                        "message": "Batch subscription deletion job created and queued for processing"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters"
        }
    }
)
async def delete_batch_subscriptions(
    payload: BatchDeleteRequest,
    http_response: Response,
    service: SubscriptionServiceProtocol = Depends(get_subscription_service),
):
    """
    Batch subscription deletion endpoint
    
    Execution path:
    1. Validate request data (Pydantic auto-validation, including count limit 1-100)
    2. Call batch_service.create_batch_delete_job() to create batch job
    3. Build response object with batch_id and status_url
    4. Return 202 Accepted status code
    
    Note: This endpoint does not wait for all subscriptions to be deleted, but returns immediately.
    The actual deletion work happens asynchronously in a background thread, and clients need to poll for status.
    """
    try:
        # Step 1-2: Create batch job (service internally starts background processing)
        # Need to pass subscription_service to batch_service
        from app.services.subscription_service import SqlAlchemySubscriptionService
        if not isinstance(service, SqlAlchemySubscriptionService):
            raise ValueError("Service type mismatch")
        
        job = batch_subscription_service.create_batch_delete_job(payload, service)
        
        # Step 3: Build response
        response_obj = BatchJobResponse(
            batch_id=job.batch_id,
            status=job.status,
            status_url=f"/subscriptions/batch/{job.batch_id}/status",
            total_count=job.total_count,
            message="Batch subscription deletion job created and queued for processing"
        )
        
        # Step 4: Return 202 Accepted
        http_response.status_code = status.HTTP_202_ACCEPTED
        return response_obj
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch deletion job: {str(e)}"
        )
