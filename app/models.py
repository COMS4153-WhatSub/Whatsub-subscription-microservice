from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

class SubscriptionCreate(BaseModel):
    user_id: str
    plan: str
    payment_method: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    status: Optional[str] = None

class SubscriptionRead(BaseModel):
    id: UUID
    user_id: str
    plan: str
    status: str
    start_date: datetime
    end_date: datetime
    renewal_date: datetime
    payment_method: Optional[str] = None

class Health(BaseModel):
    status: int
    status_message: str
    timestamp: str
    ip_address: str
    echo: Optional[str] = None
    path_echo: Optional[str] = None

class SubscriptionStats(BaseModel):
    total: int
    total_active: int
    by_plan: Dict[str, int]
    by_status: Dict[str, int]
    generated_at: datetime
