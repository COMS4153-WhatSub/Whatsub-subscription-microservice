from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class BillingType(str, Enum):
    annually = "annually"
    monthly = "monthly"
    quarterly = "quarterly"


class Category(str, Enum):
    streaming = "streaming"
    music = "music"
    software = "software"
    gaming = "gaming"
    cloud = "cloud"
    news = "news"
    fitness = "fitness"
    education = "education"
    other = "other"


class SubscriptionBase(BaseModel):
    user_id: str = Field(description="User ID (CHAR(36))")
    plan: str = Field(description="Subscription service name or plan name (e.g., 'Netflix Premium', 'Spotify Premium', 'Amazon Prime')", max_length=255)
    url: Optional[str] = Field(default=None, description="Subscription URL", max_length=500)
    account: Optional[str] = Field(default=None, description="Account identifier", max_length=255)
    billing_date: Optional[date] = Field(default=None, description="Billing date")
    price: Optional[Decimal] = Field(default=None, description="Subscription price", max_digits=10, decimal_places=2)
    category: Optional[Category] = Field(default=Category.other, description="Subscription category")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "7e98a8f7-0e22-4f4a-9f3e-5a2d7c6f9e11",
                    "plan": "Netflix Premium",
                    "url": "https://www.netflix.com",
                    "account": "user@example.com",
                    "billing_date": "2024-01-15",
                    "price": "15.99"
                }
            ]
        }
    }


class SubscriptionCreate(SubscriptionBase):
    billing_type: BillingType = Field(description="Billing frequency type")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "7e98a8f7-0e22-4f4a-9f3e-5a2d7c6f9e11",
                    "plan": "Netflix Premium",
                    "billing_type": "monthly",
                    "url": "https://www.netflix.com",
                    "account": "user@example.com",
                    "price": "15.99"
                }
            ]
        }
    }


class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = Field(default=None, description="Subscription plan name", max_length=255)
    url: Optional[str] = Field(default=None, description="Subscription URL", max_length=500)
    account: Optional[str] = Field(default=None, description="Account identifier", max_length=255)
    billing_type: Optional[BillingType] = Field(default=None, description="Billing frequency type")
    billing_date: Optional[date] = Field(default=None, description="Billing date")
    price: Optional[Decimal] = Field(default=None, description="Subscription price", max_digits=10, decimal_places=2)
    category: Optional[Category] = Field(default=None, description="Subscription category")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"plan": "Pro"},
                {"price": "25.00"},
                {"billing_date": "2024-02-15"},
                {"billing_type": "quarterly"},
            ]
        }
    }


class SubscriptionRead(SubscriptionBase):
    id: int = Field(description="Subscription ID (auto-increment)")
    billing_type: BillingType = Field(description="Billing frequency type")
    category: Optional[Category] = Field(default=Category.other, description="Subscription category")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "user_id": "7e98a8f7-0e22-4f4a-9f3e-5a2d7c6f9e11",
                    "plan": "Netflix Premium",
                    "billing_type": "monthly",
                    "url": "https://www.netflix.com",
                    "account": "user@example.com",
                    "billing_date": "2024-01-15",
                    "price": "15.99",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
    }

