from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.entities.market_item import MarketItem
from app.entities.market_price_history import MarketPriceHistory
from app.entities.market_price_latest import MarketPriceLatest
from app.entities.market_provider import MarketProvider


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class MarketRepository:
    """
    Repository for market data operations.

    Responsibilities:
    - CRUD operations for providers, items, and prices
    - Transactions
    - Upsert latest prices
    - Insert history records
    - Cache validation

    MUST NOT:
    - Access HTTP
    - Parse HTML
    - Know about specific providers
    - Contain business logic
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # Transaction Operations
    # =========================================================

    def begin_transaction(self) -> None:
        """Explicitly begin a new transaction."""
        pass  # Session already starts without autocommit

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()

    def close(self) -> None:
        """Close the database session."""
        self.db.close()

    # =========================================================
    # Provider Operations
    # =========================================================

    def get_provider(self, name: str) -> MarketProvider | None:
        """Retrieve a provider by name."""
        stmt = select(MarketProvider).where(MarketProvider.name == name)
        return self.db.scalar(stmt)

    def get_provider_by_id(self, provider_id: int) -> MarketProvider | None:
        """Retrieve a provider by ID."""
        stmt = select(MarketProvider).where(MarketProvider.id == provider_id)
        return self.db.scalar(stmt)

    def get_all_providers(
        self,
        active_only: bool = True,
    ) -> list[MarketProvider]:
        """Retrieve all providers."""
        stmt = select(MarketProvider)
        if active_only:
            stmt = stmt.where(MarketProvider.active.is_(True))
        stmt = stmt.order_by(MarketProvider.name)
        return list(self.db.scalars(stmt).all())

    def create_provider(
        self,
        name: str,
        display_name: str,
        base_url: str,
        active: bool = True,
    ) -> MarketProvider:
        """Create a new provider."""
        provider = MarketProvider(
            name=name,
            display_name=display_name,
            base_url=base_url,
            active=active,
        )
        self.db.add(provider)
        self.db.flush()  # Get the ID
        return provider

    def update_provider(
        self,
        provider_id: int,
        display_name: str | None = None,
        base_url: str | None = None,
        active: bool | None = None,
    ) -> MarketProvider | None:
        """Update an existing provider."""
        provider = self.get_provider_by_id(provider_id)
        if provider is None:
            return None

        if display_name is not None:
            provider.display_name = display_name
        if base_url is not None:
            provider.base_url = base_url
        if active is not None:
            provider.active = active

        self.db.flush()
        return provider

    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider."""
        provider = self.get_provider_by_id(provider_id)
        if provider is None:
            return False

        self.db.delete(provider)
        self.db.flush()
        return True

    # =========================================================
    # Item Operations
    # =========================================================

    def get_item(self, code: str) -> MarketItem | None:
        """Retrieve an item by code."""
        stmt = select(MarketItem).where(MarketItem.code == code)
        return self.db.scalar(stmt)

    def get_item_by_id(self, item_id: int) -> MarketItem | None:
        """Retrieve an item by ID."""
        stmt = select(MarketItem).where(MarketItem.id == item_id)
        return self.db.scalar(stmt)

    def get_all_items(self, active_only: bool = True) -> list[MarketItem]:
        """Retrieve all items."""
        stmt = select(MarketItem)
        if active_only:
            stmt = stmt.where(MarketItem.active.is_(True))
        stmt = stmt.order_by(MarketItem.code)
        return list(self.db.scalars(stmt).all())

    def get_items_by_category(self, category: str) -> list[MarketItem]:
        """Retrieve items by category."""
        stmt = (
            select(MarketItem)
            .where(MarketItem.category == category)
            .order_by(MarketItem.code)
        )
        return list(self.db.scalars(stmt).all())

    def create_item(
        self,
        code: str,
        title: str,
        category: str,
        unit: str,
        active: bool = True,
    ) -> MarketItem:
        """Create a new item."""
        item = MarketItem(
            code=code,
            title=title,
            category=category,
            unit=unit,
            active=active,
        )
        self.db.add(item)
        self.db.flush()  # Get the ID
        return item

    def update_item(
        self,
        item_id: int,
        title: str | None = None,
        category: str | None = None,
        unit: str | None = None,
        active: bool | None = None,
    ) -> MarketItem | None:
        """Update an existing item."""
        item = self.get_item_by_id(item_id)
        if item is None:
            return None

        if title is not None:
            item.title = title
        if category is not None:
            item.category = category
        if unit is not None:
            item.unit = unit
        if active is not None:
            item.active = active

        self.db.flush()
        return item

    def delete_item(self, item_id: int) -> bool:
        """Delete an item."""
        item = self.get_item_by_id(item_id)
        if item is None:
            return False

        self.db.delete(item)
        self.db.flush()
        return True

    # =========================================================
    # Latest Price Operations
    # =========================================================

    def get_latest(
        self, item_id: int, provider_id: int
    ) -> MarketPriceLatest | None:
        """Retrieve latest price for an item from a specific provider."""
        stmt = select(MarketPriceLatest).where(
            MarketPriceLatest.item_id == item_id,
            MarketPriceLatest.provider_id == provider_id,
        )
        return self.db.scalar(stmt)

    def get_latest_by_code(
        self,
        item_code: str,
        provider_name: str,
    ) -> MarketPriceLatest | None:
        """Retrieve latest price by item code and provider name."""
        stmt = (
            select(MarketPriceLatest)
            .join(MarketItem, MarketPriceLatest.item_id == MarketItem.id)
            .join(
                MarketProvider,
                MarketPriceLatest.provider_id == MarketProvider.id,
            )
            .where(
                MarketItem.code == item_code,
                MarketProvider.name == provider_name,
            )
        )
        return self.db.scalar(stmt)

    def get_all_latest(
        self,
        provider_id: int | None = None,
        item_id: int | None = None,
        category: str | None = None,
    ) -> list[MarketPriceLatest]:
        """Retrieve all latest prices with optional filtering."""
        stmt = select(MarketPriceLatest).options(
            joinedload(MarketPriceLatest.item),
            joinedload(MarketPriceLatest.provider),
        )

        if provider_id is not None:
            stmt = stmt.where(MarketPriceLatest.provider_id == provider_id)
        if item_id is not None:
            stmt = stmt.where(MarketPriceLatest.item_id == item_id)
        if category is not None:
            stmt = stmt.join(MarketItem).where(MarketItem.category == category)

        stmt = stmt.order_by(MarketPriceLatest.retrieved_at.desc())
        return list(self.db.scalars(stmt).unique().all())

    def upsert_latest(
        self,
        item_id: int,
        provider_id: int,
        price: int,
        change_value: int,
        provider_date: str | None = None,
        provider_time: str | None = None,
        raw_data: dict | None = None,
    ) -> MarketPriceLatest:
        """
        Insert or update latest price (upsert operation).

        Uses database unique constraint on (item_id, provider_id).
        """
        existing = self.get_latest(item_id, provider_id)

        if existing is not None:
            # Update existing record
            existing.price = price
            existing.change_value = change_value
            existing.provider_date = provider_date
            existing.provider_time = provider_time
            existing.raw_data = raw_data
            existing.retrieved_at = utc_now()
            return existing
        else:
            # Insert new record
            latest = MarketPriceLatest(
                item_id=item_id,
                provider_id=provider_id,
                price=price,
                change_value=change_value,
                provider_date=provider_date,
                provider_time=provider_time,
                raw_data=raw_data,
            )
            self.db.add(latest)
            self.db.flush()
            return latest

    def delete_latest(self, latest_id: int) -> bool:
        """Delete a latest price record."""
        stmt = select(MarketPriceLatest).where(MarketPriceLatest.id == latest_id)
        latest = self.db.scalar(stmt)

        if latest is None:
            return False

        self.db.delete(latest)
        self.db.flush()
        return True

    # =========================================================
    # History Price Operations
    # =========================================================

    def insert_history(
        self,
        item_id: int,
        provider_id: int,
        price: int,
        change_value: int,
        provider_date: str | None = None,
        provider_time: str | None = None,
        raw_data: dict | None = None,
        retrieved_at: datetime | None = None,
    ) -> MarketPriceHistory:
        """Insert a new historical price record."""
        history = MarketPriceHistory(
            item_id=item_id,
            provider_id=provider_id,
            price=price,
            change_value=change_value,
            provider_date=provider_date,
            provider_time=provider_time,
            raw_data=raw_data,
            retrieved_at=retrieved_at or utc_now(),
        )
        self.db.add(history)
        self.db.flush()
        return history

    def get_history(
        self,
        limit: int = 100,
        provider_id: int | None = None,
        item_id: int | None = None,
        category: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[MarketPriceHistory]:
        """Retrieve historical prices with optional filtering."""
        stmt = select(MarketPriceHistory).options(
            joinedload(MarketPriceHistory.item), joinedload(MarketPriceHistory.provider)
        )

        if provider_id is not None:
            stmt = stmt.where(MarketPriceHistory.provider_id == provider_id)
        if item_id is not None:
            stmt = stmt.where(MarketPriceHistory.item_id == item_id)
        if category is not None:
            stmt = stmt.join(MarketItem).where(MarketItem.category == category)
        if start_date is not None:
            stmt = stmt.where(MarketPriceHistory.retrieved_at >= start_date)
        if end_date is not None:
            stmt = stmt.where(MarketPriceHistory.retrieved_at <= end_date)

        stmt = stmt.order_by(MarketPriceHistory.retrieved_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_history_by_code(
        self, item_code: str, provider_name: str, limit: int = 100
    ) -> list[MarketPriceHistory]:
        """Retrieve historical prices by item code and provider name."""
        stmt = (
            select(MarketPriceHistory)
            .join(MarketItem, MarketPriceHistory.item_id == MarketItem.id)
            .join(MarketProvider, MarketPriceHistory.provider_id == MarketProvider.id)
            .where(MarketItem.code == item_code, MarketProvider.name == provider_name)
            .order_by(MarketPriceHistory.retrieved_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def cleanup_history(self, older_than_days: int = 90, batch_size: int = 1000) -> int:
        """Delete old historical records."""
        cutoff_date = utc_now() - timedelta(days=older_than_days)

        # Delete in batches to avoid locking issues
        total_deleted = 0

        while True:
            stmt = (
                select(MarketPriceHistory.id)
                .where(MarketPriceHistory.retrieved_at < cutoff_date)
                .limit(batch_size)
            )
            ids_to_delete = list(self.db.scalars(stmt).all())

            if not ids_to_delete:
                break

            del_stmt = delete(MarketPriceHistory).where(
                MarketPriceHistory.id.in_(ids_to_delete)
            )
            result = self.db.execute(del_stmt)
            total_deleted += result.rowcount or 0

        return total_deleted

    # =========================================================
    # Caching Operations
    # =========================================================

    def is_cache_valid(
        self, latest: MarketPriceLatest | None, minutes: int = 5
    ) -> bool:
        """Check if cached latest price is still valid."""
        if latest is None:
            return False

        retrieved_at = latest.retrieved_at
        # Normalize timezone-naive datetimes to UTC
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

        return retrieved_at >= (utc_now() - timedelta(minutes=minutes))
