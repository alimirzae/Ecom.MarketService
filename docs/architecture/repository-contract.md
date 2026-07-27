# Repository Contract

This document defines the public interface contract for the `MarketRepository` class.

The Repository Layer is responsible for all database operations using SQLAlchemy.

---

## Responsibilities

- **CRUD Operations**: Create, Read, Update, Delete for all entities
- **Transactions**: Begin, commit, and rollback database transactions
- **Upsert Latest**: Insert or update latest prices with unique constraint handling
- **History Management**: Insert historical price records
- **Lookups**: Provider and item lookups by name/code
- **Caching Support**: Cache validation checks
- **Queries**: Complex queries for history and latest prices

---

## Non-Responsibilities (MUST NOT)

- **NO HTTP Access**: Repository must never call external APIs
- **NO HTML Parsing**: Repository must never parse HTML or web content
- **NO Provider Knowledge**: Repository must not know about specific providers
- **NO FastAPI Logic**: Repository must not contain API-specific logic
- **NO Business Logic**: Repository must not contain business rules

---

## Public Interface: `IMarketRepository`

### Provider Operations

```python
def get_provider(self, name: str) -> MarketProvider | None:
    """
    Retrieve a provider by name.
    
    Args:
        name: Provider name (e.g., 'navasan')
    
    Returns:
        MarketProvider entity or None if not found
    """
```

```python
def get_provider_by_id(self, provider_id: int) -> MarketProvider | None:
    """
    Retrieve a provider by ID.
    
    Args:
        provider_id: Provider primary key
    
    Returns:
        MarketProvider entity or None if not found
    """
```

```python
def get_all_providers(self, active_only: bool = True) -> list[MarketProvider]:
    """
    Retrieve all providers.
    
    Args:
        active_only: If True, only return active providers
    
    Returns:
        List of MarketProvider entities
    """
```

```python
def create_provider(
    self,
    name: str,
    display_name: str,
    base_url: str,
    active: bool = True
) -> MarketProvider:
    """
    Create a new provider.
    
    Args:
        name: Provider identifier name
        display_name: Human-readable name
        base_url: Base URL for the provider
        active: Whether provider is active
    
    Returns:
        Created MarketProvider entity
    """
```

```python
def update_provider(
    self,
    provider_id: int,
    display_name: str | None = None,
    base_url: str | None = None,
    active: bool | None = None
) -> MarketProvider | None:
    """
    Update an existing provider.
    
    Args:
        provider_id: Provider primary key
        display_name: New display name (optional)
        base_url: New base URL (optional)
        active: New active status (optional)
    
    Returns:
        Updated MarketProvider entity or None if not found
    """
```

```python
def delete_provider(self, provider_id: int) -> bool:
    """
    Delete a provider.
    
    Args:
        provider_id: Provider primary key
    
    Returns:
        True if deleted, False if not found
    """
```

---

### Item Operations

```python
def get_item(self, code: str) -> MarketItem | None:
    """
    Retrieve an item by code.
    
    Args:
        code: Item code (e.g., 'usd', 'sekkeh')
    
    Returns:
        MarketItem entity or None if not found
    """
```

```python
def get_item_by_id(self, item_id: int) -> MarketItem | None:
    """
    Retrieve an item by ID.
    
    Args:
        item_id: Item primary key
    
    Returns:
        MarketItem entity or None if not found
    """
```

```python
def get_all_items(self, active_only: bool = True) -> list[MarketItem]:
    """
    Retrieve all items.
    
    Args:
        active_only: If True, only return active items
    
    Returns:
        List of MarketItem entities
    """
```

```python
def get_items_by_category(self, category: str) -> list[MarketItem]:
    """
    Retrieve items by category.
    
    Args:
        category: Item category (e.g., 'currency', 'gold', 'coin')
    
    Returns:
        List of MarketItem entities
    """
```

```python
def create_item(
    self,
    code: str,
    title: str,
    category: str,
    unit: str,
    active: bool = True
) -> MarketItem:
    """
    Create a new item.
    
    Args:
        code: Item code identifier
        title: Item title/name
        category: Item category
        unit: Unit of measurement
        active: Whether item is active
    
    Returns:
        Created MarketItem entity
    """
```

```python
def update_item(
    self,
    item_id: int,
    title: str | None = None,
    category: str | None = None,
    unit: str | None = None,
    active: bool | None = None
) -> MarketItem | None:
    """
    Update an existing item.
    
    Args:
        item_id: Item primary key
        title: New title (optional)
        category: New category (optional)
        unit: New unit (optional)
        active: New active status (optional)
    
    Returns:
        Updated MarketItem entity or None if not found
    """
```

```python
def delete_item(self, item_id: int) -> bool:
    """
    Delete an item.
    
    Args:
        item_id: Item primary key
    
    Returns:
        True if deleted, False if not found
    """
```

---

### Latest Price Operations

```python
def get_latest(
    self,
    item_id: int,
    provider_id: int
) -> MarketPriceLatest | None:
    """
    Retrieve latest price for an item from a specific provider.
    
    Args:
        item_id: Item primary key
        provider_id: Provider primary key
    
    Returns:
        MarketPriceLatest entity or None if not found
    """
```

```python
def get_latest_by_code(
    self,
    item_code: str,
    provider_name: str
) -> MarketPriceLatest | None:
    """
    Retrieve latest price by item code and provider name.
    
    Args:
        item_code: Item code (e.g., 'usd')
        provider_name: Provider name (e.g., 'navasan')
    
    Returns:
        MarketPriceLatest entity or None if not found
    """
```

```python
def get_all_latest(
    self,
    provider_id: int | None = None,
    item_id: int | None = None,
    category: str | None = None
) -> list[MarketPriceLatest]:
    """
    Retrieve all latest prices with optional filtering.
    
    Args:
        provider_id: Filter by provider (optional)
        item_id: Filter by item (optional)
        category: Filter by item category (optional)
    
    Returns:
        List of MarketPriceLatest entities
    """
```

```python
def upsert_latest(
    self,
    item_id: int,
    provider_id: int,
    price: int,
    change_value: int,
    provider_date: str | None = None,
    provider_time: str | None = None,
    raw_data: dict | None = None
) -> MarketPriceLatest:
    """
    Insert or update latest price (upsert operation).
    
    Uses database unique constraint on (item_id, provider_id).
    Updates existing record or inserts new one.
    
    Args:
        item_id: Item primary key
        provider_id: Provider primary key
        price: Current price value
        change_value: Price change amount
        provider_date: Provider's date string (optional)
        provider_time: Provider's time string (optional)
        raw_data: Original raw data from provider (optional)
    
    Returns:
        MarketPriceLatest entity (inserted or updated)
    """
```

```python
def delete_latest(self, latest_id: int) -> bool:
    """
    Delete a latest price record.
    
    Args:
        latest_id: Latest price primary key
    
    Returns:
        True if deleted, False if not found
    """
```

---

### History Price Operations

```python
def insert_history(
    self,
    item_id: int,
    provider_id: int,
    price: int,
    change_value: int,
    provider_date: str | None = None,
    provider_time: str | None = None,
    raw_data: dict | None = None,
    retrieved_at: datetime | None = None
) -> MarketPriceHistory:
    """
    Insert a new historical price record.
    
    Args:
        item_id: Item primary key
        provider_id: Provider primary key
        price: Historical price value
        change_value: Historical price change
        provider_date: Provider's date string (optional)
        provider_time: Provider's time string (optional)
        raw_data: Original raw data (optional)
        retrieved_at: Timestamp (defaults to now)
    
    Returns:
        Created MarketPriceHistory entity
    """
```

```python
def get_history(
    self,
    limit: int = 100,
    provider_id: int | None = None,
    item_id: int | None = None,
    category: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None
) -> list[MarketPriceHistory]:
    """
    Retrieve historical prices with optional filtering.
    
    Args:
        limit: Maximum number of records to return
        provider_id: Filter by provider (optional)
        item_id: Filter by item (optional)
        category: Filter by item category (optional)
        start_date: Start date filter (optional)
        end_date: End date filter (optional)
    
    Returns:
        List of MarketPriceHistory entities (ordered by retrieved_at DESC)
    """
```

```python
def get_history_by_code(
    self,
    item_code: str,
    provider_name: str,
    limit: int = 100
) -> list[MarketPriceHistory]:
    """
    Retrieve historical prices by item code and provider name.
    
    Args:
        item_code: Item code (e.g., 'usd')
        provider_name: Provider name (e.g., 'navasan')
        limit: Maximum number of records
    
    Returns:
        List of MarketPriceHistory entities (ordered by retrieved_at DESC)
    """
```

```python
def cleanup_history(
    self,
    older_than_days: int = 90,
    batch_size: int = 1000
) -> int:
    """
    Delete old historical records.
    
    Args:
        older_than_days: Delete records older than this many days
        batch_size: Number of records to delete per batch
    
    Returns:
        Total number of deleted records
    """
```

---

### Caching Operations

```python
def is_cache_valid(
    self,
    latest: MarketPriceLatest | None,
    minutes: int = 5
) -> bool:
    """
    Check if cached latest price is still valid.
    
    Args:
        latest: Latest price entity to check
        minutes: Cache validity duration in minutes
    
    Returns:
        True if cache is valid, False otherwise
    """
```

---

### Transaction Operations

```python
def begin_transaction(self) -> None:
    """
    Explicitly begin a new transaction.
    
    Note: Session starts without autocommit, so this is mainly
    for explicit control and clarity.
    """
```

```python
def commit(self) -> None:
    """
    Commit the current transaction.
    
    Persists all pending changes to the database.
    """
```

```python
def rollback(self) -> None:
    """
    Rollback the current transaction.
    
    Discards all pending changes since last commit/rollback.
    """
```

```python
def close(self) -> None:
    """
    Close the database session.
    
    Should be called when repository is no longer needed.
    """
```

---

## Usage Example

```python
from app.database.database import SessionLocal
from app.repository.market_repository import MarketRepository

# Create session and repository
db = SessionLocal()
repo = MarketRepository(db)

try:
    # Begin transaction
    repo.begin_transaction()
    
    # Upsert latest price
    latest = repo.upsert_latest(
        item_id=1,
        provider_id=1,
        price=58000,
        change_value=500,
        provider_time="14:30"
    )
    
    # Insert history record
    repo.insert_history(
        item_id=1,
        provider_id=1,
        price=58000,
        change_value=500
    )
    
    # Commit transaction
    repo.commit()
    
except Exception as e:
    # Rollback on error
    repo.rollback()
    raise
    
finally:
    # Always close session
    repo.close()
```

---

## Implementation Notes

1. **SQLAlchemy 2.x Style**: All queries use SQLAlchemy 2.0+ syntax with `select()` constructs
2. **Type Hints**: All methods include complete type annotations
3. **No Business Logic**: Repository only handles data access, no business rules
4. **Transaction Safety**: All write operations should be wrapped in transactions
5. **Upsert Strategy**: Uses SQLAlchemy `merge()` for upsert operations respecting unique constraints
6. **Eager Loading**: Consider using `options(joinedload())` for related entities when needed
7. **Batch Operations**: For bulk inserts/updates, use `bulk_insert_mappings()` for performance

---

## Error Handling

- **NotFoundError**: Return `None` for single-entity lookups when not found
- **Empty List**: Return empty list `[]` for multi-entity queries when no results
- **Constraint Violations**: Let SQLAlchemy raise integrity errors for constraint violations
- **Transaction Errors**: Rollback on any exception during transaction

---

## Version

- **Document Version**: 1.0
- **Last Updated**: 2024
- **Status**: Approved for Implementation
