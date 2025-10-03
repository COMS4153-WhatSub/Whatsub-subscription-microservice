from uuid import UUID
from typing import Dict
from app.models import SubscriptionRead

# Fake in-memory DB
subscriptions: Dict[UUID, SubscriptionRead] = {}
