from uuid import UUID
from typing import Dict
from app.models import SubscriptionRead

# in-memory store
subscriptions: Dict[UUID, SubscriptionRead] = {}
