from uuid import UUID
from typing import Dict
from app.models import SubscriptionRead
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from app.models import BillingType

# in-memory store
subscriptions: Dict[UUID, SubscriptionRead] = {}

# Preload some fake data
sub1_id = uuid4()
sub2_id = uuid4()

subscriptions[sub1_id] = SubscriptionRead(
    id=sub1_id,
    user_id="user_01",
    plan="Basic",
    start_date=datetime.utcnow(),
    end_date=datetime.utcnow() + timedelta(days=30),
    billing_date=datetime.utcnow(),
    price=Decimal("10.00"),
    account="default",
    billing_type=BillingType.monthly,
)

subscriptions[sub2_id] = SubscriptionRead(
    id=sub2_id,
    user_id="user_02",
    plan="Pro",
    start_date=datetime.utcnow(),
    end_date=datetime.utcnow() + timedelta(days=365),
    billing_date=datetime.utcnow(),
    price=Decimal("99.00"),
    account="default",
    billing_type=BillingType.annually,
)
