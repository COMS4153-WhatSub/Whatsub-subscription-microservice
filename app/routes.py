from fastapi import APIRouter, HTTPException, Query, Path, Response
from uuid import UUID
from typing import List, Optional
from app import crud, models, health

router = APIRouter()

# Health endpoints
@router.get("/health", response_model=models.Health)
def get_health_no_path(echo: Optional[str] = Query(None)):
    return health.make_health(echo=echo)

@router.get("/health/{path_echo}", response_model=models.Health)
def get_health_with_path(
    path_echo: str = Path(...),
    echo: Optional[str] = Query(None),
):
    return health.make_health(echo=echo, path_echo=path_echo)

# Subscription endpoints
@router.post("/subscriptions", response_model=models.SubscriptionRead, status_code=201)
def create_subscription(sub: models.SubscriptionCreate):
    return crud.create_subscription(sub)

@router.get("/subscriptions", response_model=List[models.SubscriptionRead])
def list_subscriptions(user_id: Optional[str] = Query(None)):
    return crud.list_subscriptions(user_id)

@router.get("/subscriptions/{sub_id}", response_model=models.SubscriptionRead)
def get_subscription(sub_id: UUID):
    sub = crud.get_subscription(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.put("/subscriptions/{sub_id}", response_model=models.SubscriptionRead)
def update_subscription(sub_id: UUID, sub_update: models.SubscriptionUpdate):
    sub = crud.update_subscription(sub_id, sub_update)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.delete("/subscriptions/{sub_id}", status_code=204)
def delete_subscription(sub_id: UUID):
    success = crud.delete_subscription(sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return Response(status_code=204)

# Root
@router.get("/")
def root():
    return {"message": "Welcome to the Subscription API. See /docs for OpenAPI UI."}
