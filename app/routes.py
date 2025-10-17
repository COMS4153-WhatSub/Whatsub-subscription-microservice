from fastapi import APIRouter, HTTPException, Query, Path, Response
from uuid import UUID
from typing import List, Optional

from app import crud, models, health, notify

router = APIRouter()

# ------------------------
# Health endpoints
# ------------------------
@router.get("/health", response_model=models.Health)
def get_health_no_path(echo: Optional[str] = Query(None)):
    return health.make_health(echo=echo)


@router.get("/health/{path_echo}", response_model=models.Health)
def get_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None),
):
    return health.make_health(echo=echo, path_echo=path_echo)


# ------------------------
# Subscription endpoints
# ------------------------
@router.post("/subscriptions", response_model=models.SubscriptionRead, status_code=201)
def create_subscription(sub: models.SubscriptionCreate):
    """Create a new subscription"""
    created = crud.create_subscription(sub)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create subscription")
    return created


@router.get("/subscriptions", response_model=List[models.SubscriptionRead])
def list_subscriptions(user_id: Optional[str] = Query(None)):
    """List subscriptions (optionally filtered by user_id)"""
    return crud.list_subscriptions(user_id)


@router.get("/subscriptions/{sub_id}", response_model=models.SubscriptionRead)
def get_subscription(sub_id: UUID):
    """Retrieve a single subscription by ID"""
    sub = crud.get_subscription(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.patch("/subscriptions/{sub_id}", response_model=models.SubscriptionRead)
def update_subscription(sub_id: UUID, sub_update: models.SubscriptionUpdate):
    """Update specific fields of a subscription"""
    sub = crud.update_subscription(sub_id, sub_update)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.delete("/subscriptions/{sub_id}", status_code=204)
def delete_subscription(sub_id: UUID):
    """Delete a subscription"""
    success = crud.delete_subscription(sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return Response(status_code=204)


# ------------------------
# Stats endpoints
# ------------------------
@router.get("/subscriptions/stats", response_model=models.SubscriptionStats)
def get_stats():
    """Return aggregated subscription statistics"""
    stats = crud.get_subscription_stats()
    return models.SubscriptionStats(**stats)


@router.post("/subscriptions/notify_counts")
def post_notify_counts():
    """Trigger sending subscription count summary to notification service"""
    try:
        resp = notify.notify_counts()
        return {"status": "sent", "http_status": resp.status_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------
# Root endpoint
# ------------------------
@router.get("/")
def root():
    return {"message": "Welcome to the Subscription API. See /docs for OpenAPI UI."}
