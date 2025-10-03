from datetime import datetime, timedelta
from uuid import UUID, uuid4
from app.models import SubscriptionCreate, SubscriptionUpdate, SubscriptionRead
from app.fake_db import subscriptions

def create_subscription(sub: SubscriptionCreate) -> SubscriptionRead:
    sub_id = uuid4()
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    subscription = SubscriptionRead(
        id=sub_id,
        user_id=sub.user_id,
        plan=sub.plan,
        status="active",
        start_date=start_date,
        end_date=end_date,
        renewal_date=end_date,
        payment_method=sub.payment_method
    )
    subscriptions[sub_id] = subscription
    return subscription

def get_subscription(sub_id: UUID) -> SubscriptionRead | None:
    return subscriptions.get(sub_id)

def list_subscriptions(user_id: str | None = None):
    results = list(subscriptions.values())
    if user_id:
        results = [s for s in results if s.user_id == user_id]
    return results

def update_subscription(sub_id: UUID, sub_update: SubscriptionUpdate) -> SubscriptionRead | None:
    sub = subscriptions.get(sub_id)
    if not sub:
        return None
    if sub_update.plan:
        sub.plan = sub_update.plan
    if sub_update.status:
        sub.status = sub_update.status
    subscriptions[sub_id] = sub
    return sub

def delete_subscription(sub_id: UUID) -> bool:
    if sub_id in subscriptions:
        del subscriptions[sub_id]
        return True
    return False
