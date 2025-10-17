from datetime import datetime, timedelta
from uuid import UUID, uuid4
from collections import Counter
from typing import Dict, Optional

from app.models import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionRead,
    BillingType,
)
from app.fake_db import subscriptions


def create_subscription(sub: SubscriptionCreate) -> SubscriptionRead:
    """Create a new subscription entry in the fake DB."""
    sub_id = uuid4()
    start_date = datetime.utcnow()

    # determine subscription period based on billing type
    if sub.billing_type == BillingType.monthly:
        end_date = start_date + timedelta(days=30)
    elif sub.billing_type == BillingType.quarterly:
        end_date = start_date + timedelta(days=90)
    else:  # annually
        end_date = start_date + timedelta(days=365)

    # billing date = start_date (first charge)
    billing_date = start_date

    # fallback price if not given
    price = sub.price if sub.price is not None else _default_price(sub.plan)

    # create SubscriptionRead object
    subscription = SubscriptionRead(
        id=sub_id,
        user_id=sub.user_id,
        plan=sub.plan,
        start_date=start_date,
        end_date=end_date,
        billing_date=billing_date,
        price=price,
        account="default",  # placeholder
        billing_type=sub.billing_type,
    )

    subscriptions[sub_id] = subscription
    return subscription


def get_subscription(sub_id: UUID) -> Optional[SubscriptionRead]:
    return subscriptions.get(sub_id)


def list_subscriptions(user_id: Optional[str] = None):
    results = list(subscriptions.values())
    if user_id:
        results = [s for s in results if s.user_id == user_id]
    return results


def update_subscription(sub_id: UUID, sub_update: SubscriptionUpdate) -> Optional[SubscriptionRead]:
    sub = subscriptions.get(sub_id)
    if not sub:
        return None

    if sub_update.plan is not None:
        sub.plan = sub_update.plan
    if sub_update.billing_type is not None:
        sub.billing_type = sub_update.billing_type
    if sub_update.end_date is not None:
        sub.end_date = sub_update.end_date
    if sub_update.price is not None:
        sub.price = sub_update.price

    subscriptions[sub_id] = sub
    return sub


def delete_subscription(sub_id: UUID) -> bool:
    if sub_id in subscriptions:
        del subscriptions[sub_id]
        return True
    return False


def get_subscription_stats() -> Dict:
    """Aggregate subscription statistics."""
    subs = list(subscriptions.values())
    total = len(subs)

    by_plan = dict(Counter(s.plan for s in subs))
    by_billing_type = dict(Counter(s.billing_type for s in subs))

    # since 'status' is removed, use a placeholder
    by_status = {"active": total}

    return {
        "total": total,
        "total_active": total,  # all active for now
        "by_plan": by_plan,
        "by_status": by_status,
        "generated_at": datetime.utcnow(),
    }


# internal helper
def _default_price(plan: str):
    """Set simple default price logic per plan."""
    default_prices = {
        "basic": 10.00,
        "pro": 25.00,
        "enterprise": 99.00,
    }
    return default_prices.get(plan.lower(), 15.00)
