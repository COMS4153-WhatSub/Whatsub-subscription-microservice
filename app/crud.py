from datetime import datetime, timedelta
from uuid import UUID, uuid4
from collections import Counter
from typing import Dict

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

def get_subscription_stats() -> Dict:
    """
    Return stats dict:
    {
      "total": int,
      "total_active": int,
      "by_plan": {plan: count, ...},
      "by_status": {status: count, ...},
      "generated_at": datetime
    }
    """
    subs = list(subscriptions.values())
    total = len(subs)
    total_active = sum(1 for s in subs if s.status == "active")
    by_plan = dict(Counter(s.plan for s in subs))
    by_status = dict(Counter(s.status for s in subs))
    return {
        "total": total,
        "total_active": total_active,
        "by_plan": by_plan,
        "by_status": by_status,
        "generated_at": datetime.utcnow()
    }
