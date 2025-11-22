from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Date, Integer, Numeric, Index, Enum as SQLEnum
from datetime import datetime, date
from decimal import Decimal
import enum


class BillingTypeEnum(str, enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    annually = "annually"


class CategoryEnum(str, enum.Enum):
    streaming = "streaming"
    music = "music"
    software = "software"
    gaming = "gaming"
    cloud = "cloud"
    news = "news"
    fitness = "fitness"
    education = "education"
    other = "other"


class Base(DeclarativeBase):
    pass


class SubscriptionORM(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_type: Mapped[str] = mapped_column(
        SQLEnum(BillingTypeEnum, native_enum=False, length=20),
        nullable=False
    )
    billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    category: Mapped[str | None] = mapped_column(
        SQLEnum(CategoryEnum, native_enum=False, length=20),
        nullable=True,
        default="other"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_billing_date', 'billing_date'),
        Index('idx_billing_type', 'billing_type'),
        Index('idx_category', 'category'),
    )

