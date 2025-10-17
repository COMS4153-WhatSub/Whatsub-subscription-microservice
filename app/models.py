from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from decimal import Decimal
from enum import Enum

class BillingType(str, Enum):
    annually = "annually"
    monthly = "monthly"
    quarterly = "quarterly"

class SubscriptionCreate(BaseModel):
    user_id: str
    plan: str
    billing_type: BillingType
    price: Optional[Decimal] = None  

class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    billing_type: Optional[BillingType] = None
    end_date: Optional[datetime] = None
    price: Optional[Decimal] = None

# Delete status, renewal_date, payment_method
class SubscriptionRead(BaseModel):
    id: UUID
    user_id: str
    plan: str
    start_date: datetime
    end_date: datetime
    billing_date: datetime
    price: Decimal
    account: str
    billing_type: BillingType

class Health(BaseModel):
    status: int
    status_message: str
    timestamp: datetime
    ip_address: str
    echo: Optional[str] = None
    path_echo: Optional[str] = None

class SubscriptionStats(BaseModel):
    total: int
    total_active: int
    by_plan: Dict[str, int]
    by_status: Dict[str, int]
    generated_at: datetime
