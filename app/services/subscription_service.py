from typing import List, Optional, Protocol, Callable
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy import or_

from app.models.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionRead, BillingType
from app.models.common import PaginatedResponse
from app.services.orm_models import SubscriptionORM


class SubscriptionServiceProtocol(Protocol):
    def list_subscriptions(
        self,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
        account: Optional[str] = None,
        billing_date_from: Optional[date] = None,
        billing_date_to: Optional[date] = None,
        price_min: Optional[Decimal] = None,
        price_max: Optional[Decimal] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[SubscriptionRead]:
        ...

    def get_subscription(self, subscription_id: int) -> Optional[SubscriptionRead]:
        ...

    def create_subscription(self, payload: SubscriptionCreate) -> SubscriptionRead:
        ...

    def update_subscription(self, subscription_id: int, payload: SubscriptionUpdate) -> Optional[SubscriptionRead]:
        ...

    def delete_subscription(self, subscription_id: int) -> bool:
        ...


class SqlAlchemySubscriptionService:
    def __init__(self, logger, session_factory: Callable[[], Session]):
        self.logger = logger
        self.session_factory = session_factory

    def list_subscriptions(
        self,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
        account: Optional[str] = None,
        billing_date_from: Optional[date] = None,
        billing_date_to: Optional[date] = None,
        price_min: Optional[Decimal] = None,
        price_max: Optional[Decimal] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[SubscriptionRead]:
        with self.session_factory() as session:
            query = session.query(SubscriptionORM)
            
            # Apply filters
            query = self._apply_filters(
                query,
                user_id=user_id,
                plan=plan,
                account=account,
                billing_date_from=billing_date_from,
                billing_date_to=billing_date_to,
                price_min=price_min,
                price_max=price_max,
                search=search,
            )
            
            # Get total count before pagination
            total = query.count()
            
            # Apply sorting
            query = self._apply_sorting(query, sort_by, sort_order)
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # Execute query
            rows = query.all()
            items = [self._orm_to_read(row) for row in rows]
            
            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            
            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
            )
    
    def _apply_filters(
        self,
        query,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
        account: Optional[str] = None,
        billing_date_from: Optional[date] = None,
        billing_date_to: Optional[date] = None,
        price_min: Optional[Decimal] = None,
        price_max: Optional[Decimal] = None,
        search: Optional[str] = None,
    ):
        """Apply filtering conditions to the query."""
        if user_id:
            query = query.filter(SubscriptionORM.user_id == user_id)
        
        if plan:
            query = query.filter(SubscriptionORM.name.ilike(f"%{plan}%"))
        
        if account:
            query = query.filter(SubscriptionORM.account == account)
        
        if billing_date_from:
            query = query.filter(SubscriptionORM.billing_date >= billing_date_from)
        
        if billing_date_to:
            query = query.filter(SubscriptionORM.billing_date <= billing_date_to)
        
        if price_min is not None:
            query = query.filter(SubscriptionORM.price >= price_min)
        
        if price_max is not None:
            query = query.filter(SubscriptionORM.price <= price_max)
        
        if search:
            # Search in plan name and account
            search_filter = or_(
                SubscriptionORM.name.ilike(f"%{search}%"),
                SubscriptionORM.account.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)
        
        return query
    
    def _apply_sorting(self, query, sort_by: Optional[str] = None, sort_order: Optional[str] = None):
        """Apply sorting to the query."""
        # Default sorting by created_at descending (newest first)
        if not sort_by:
            return query.order_by(SubscriptionORM.created_at.desc())
        
        # Map sort_by field names to ORM columns
        sort_mapping = {
            "id": SubscriptionORM.subscription_id,
            "user_id": SubscriptionORM.user_id,
            "plan": SubscriptionORM.name,
            "account": SubscriptionORM.account,
            "billing_date": SubscriptionORM.billing_date,
            "price": SubscriptionORM.price,
            "created_at": SubscriptionORM.created_at,
        }
        
        sort_column = sort_mapping.get(sort_by.lower())
        if not sort_column:
            # Invalid sort_by, use default
            return query.order_by(SubscriptionORM.created_at.desc())
        
        # Apply sort order
        if sort_order and sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        return query

    def get_subscription(self, subscription_id: int) -> Optional[SubscriptionRead]:
        with self.session_factory() as session:
            row = session.get(SubscriptionORM, subscription_id)
            if not row:
                return None
            return self._orm_to_read(row)

    def create_subscription(self, payload: SubscriptionCreate) -> SubscriptionRead:
        with self.session_factory() as session:
            try:
                # Calculate billing_date from billing_type if not provided
                billing_date = payload.billing_date
                if billing_date is None:
                    billing_date = self._calculate_billing_date(payload.billing_type)
                
                # Use default price if not provided
                price = payload.price
                if price is None:
                    price = self._default_price(payload.plan)
                
                # Use default account if not provided
                account = payload.account or "default"
                
                new_row = SubscriptionORM(
                    user_id=payload.user_id,
                    name=payload.plan,  # Map plan to name
                    url=payload.url,
                    account=account,
                    billing_type=payload.billing_type.value,  # Store billing_type
                    billing_date=billing_date,
                    price=price,
                )
                session.add(new_row)
                session.commit()
                session.refresh(new_row)
                self.logger.info("subscription_created", subscription_id=new_row.subscription_id, user_id=payload.user_id)
                return self._orm_to_read(new_row)
            except IntegrityError as e:
                session.rollback()
                # Log integrity errors but let component microservice handle foreign key validation
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                self.logger.error("database_integrity_error", error=error_msg, user_id=payload.user_id)
                raise ValueError(f"Database constraint violation: {error_msg}") from e
            except DatabaseError as e:
                session.rollback()
                self.logger.error("database_error", error=str(e))
                raise RuntimeError(f"Database error: {str(e)}") from e

    def update_subscription(self, subscription_id: int, payload: SubscriptionUpdate) -> Optional[SubscriptionRead]:
        with self.session_factory() as session:
            try:
                row = session.get(SubscriptionORM, subscription_id)
                if not row:
                    return None
                
                if payload.plan is not None:
                    row.name = payload.plan  # Map plan to name
                if payload.url is not None:
                    row.url = payload.url
                if payload.account is not None:
                    row.account = payload.account
                if payload.billing_type is not None:
                    row.billing_type = payload.billing_type.value
                    # If billing_type changes and billing_date is not explicitly set, recalculate it
                    if payload.billing_date is None:
                        row.billing_date = self._calculate_billing_date(payload.billing_type)
                if payload.billing_date is not None:
                    row.billing_date = payload.billing_date
                if payload.price is not None:
                    row.price = payload.price
                
                session.add(row)
                session.commit()
                session.refresh(row)
                self.logger.info("subscription_updated", subscription_id=subscription_id)
                return self._orm_to_read(row)
            except DatabaseError as e:
                session.rollback()
                self.logger.error("database_error", error=str(e))
                raise RuntimeError(f"Database error: {str(e)}") from e

    def delete_subscription(self, subscription_id: int) -> bool:
        with self.session_factory() as session:
            try:
                row = session.get(SubscriptionORM, subscription_id)
                if not row:
                    return False
                session.delete(row)
                session.commit()
                self.logger.info("subscription_deleted", subscription_id=subscription_id)
                return True
            except DatabaseError as e:
                session.rollback()
                self.logger.error("database_error", error=str(e))
                raise RuntimeError(f"Database error: {str(e)}") from e

    def _orm_to_read(self, row: SubscriptionORM) -> SubscriptionRead:
        """Convert ORM model to Pydantic read model."""
        from app.models.subscription import BillingType
        return SubscriptionRead(
            id=row.subscription_id,
            user_id=row.user_id,
            plan=row.name,  # Map name to plan
            url=row.url,
            account=row.account,
            billing_type=BillingType(row.billing_type),  # Convert string to enum
            billing_date=row.billing_date,
            price=row.price,
            created_at=row.created_at,
        )

    def _calculate_billing_date(self, billing_type: BillingType) -> date:
        """
        Calculate the next billing date based on billing type.
        
        For notification purposes, this should be the NEXT billing date,
        not the current billing cycle start date.
        """
        today = date.today()
        
        if billing_type == BillingType.monthly:
            # Next month's first day
            if today.month == 12:
                # December -> January of next year
                return date(today.year + 1, 1, 1)
            else:
                # Next month
                return date(today.year, today.month + 1, 1)
        elif billing_type == BillingType.quarterly:
            # Next quarter's first day
            current_quarter = ((today.month - 1) // 3) + 1  # 1-4
            if current_quarter == 4:
                # Q4 -> Q1 of next year
                return date(today.year + 1, 1, 1)
            else:
                # Next quarter: Q1->Apr(4), Q2->Jul(7), Q3->Oct(10)
                next_quarter_month = current_quarter * 3 + 1
                return date(today.year, next_quarter_month, 1)
        else:  # annually
            # January 1st of next year
            return date(today.year + 1, 1, 1)

    def _default_price(self, plan: str) -> Decimal:
        """Set simple default price logic per plan."""
        default_prices = {
            "basic": Decimal("10.00"),
            "pro": Decimal("25.00"),
            "enterprise": Decimal("99.00"),
        }
        return default_prices.get(plan.lower(), Decimal("15.00"))

