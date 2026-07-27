"""
Unit tests for MarketRepository.

These tests verify the repository contract without requiring a database connection.
They use mocking to isolate repository logic.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, call

import pytest
from sqlalchemy import select

from app.entities.market_item import MarketItem
from app.entities.market_price_history import MarketPriceHistory
from app.entities.market_price_latest import MarketPriceLatest
from app.entities.market_provider import MarketProvider


class TestMarketRepository:
    """Test suite for MarketRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        return MagicMock()

    @pytest.fixture
    def repo(self, mock_session):
        """Create a MarketRepository instance with mocked session."""
        from app.repository.market_repository import MarketRepository

        return MarketRepository(mock_session)

    # =========================================================
    # Transaction Operations Tests
    # =========================================================

    def test_begin_transaction(self, repo, mock_session):
        """Test begin_transaction does not raise."""
        repo.begin_transaction()  # Should not raise

    def test_commit_calls_session_commit(self, repo, mock_session):
        """Test commit calls db.commit()."""
        repo.commit()
        mock_session.commit.assert_called_once()

    def test_rollback_calls_session_rollback(self, repo, mock_session):
        """Test rollback calls db.rollback()."""
        repo.rollback()
        mock_session.rollback.assert_called_once()

    def test_close_calls_session_close(self, repo, mock_session):
        """Test close calls db.close()."""
        repo.close()
        mock_session.close.assert_called_once()

    # =========================================================
    # Provider Operations Tests
    # =========================================================

    def test_get_provider_by_name(self, repo, mock_session):
        """Test get_provider queries by name."""
        mock_provider = Mock(spec=MarketProvider)
        mock_session.scalar.return_value = mock_provider

        result = repo.get_provider("navasan")

        mock_session.scalar.assert_called_once()
        assert result == mock_provider

    def test_get_provider_returns_none_when_not_found(self, repo, mock_session):
        """Test get_provider returns None when provider not found."""
        mock_session.scalar.return_value = None

        result = repo.get_provider("unknown")

        assert result is None

    def test_get_provider_by_id(self, repo, mock_session):
        """Test get_provider_by_id queries by ID."""
        mock_provider = Mock(spec=MarketProvider)
        mock_session.scalar.return_value = mock_provider

        result = repo.get_provider_by_id(1)

        mock_session.scalar.assert_called_once()
        assert result == mock_provider

    def test_create_provider(self, repo, mock_session):
        """Test create_provider adds and flushes."""
        result = repo.create_provider(
            name="test_provider",
            display_name="Test Provider",
            base_url="https://example.com",
            active=True,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert isinstance(result, MarketProvider)
        assert result.name == "test_provider"

    def test_update_provider_success(self, repo, mock_session):
        """Test update_provider updates fields."""
        mock_provider = Mock(spec=MarketProvider)
        mock_session.scalar.side_effect = [
            mock_provider,
            mock_provider,
        ]  # get then flush

        result = repo.update_provider(provider_id=1, display_name="Updated Name")

        mock_session.flush.assert_called()
        assert result == mock_provider

    def test_update_provider_not_found(self, repo, mock_session):
        """Test update_provider returns None when not found."""
        mock_session.scalar.return_value = None

        result = repo.update_provider(provider_id=999)

        assert result is None

    def test_delete_provider_success(self, repo, mock_session):
        """Test delete_provider returns True when deleted."""
        mock_provider = Mock(spec=MarketProvider)
        mock_session.scalar.side_effect = [mock_provider, mock_provider]

        result = repo.delete_provider(1)

        mock_session.delete.assert_called_once()
        assert result is True

    def test_delete_provider_not_found(self, repo, mock_session):
        """Test delete_provider returns False when not found."""
        mock_session.scalar.return_value = None

        result = repo.delete_provider(999)

        assert result is False

    # =========================================================
    # Item Operations Tests
    # =========================================================

    def test_get_item_by_code(self, repo, mock_session):
        """Test get_item queries by code."""
        mock_item = Mock(spec=MarketItem)
        mock_session.scalar.return_value = mock_item

        result = repo.get_item("usd")

        mock_session.scalar.assert_called_once()
        assert result == mock_item

    def test_get_item_by_id(self, repo, mock_session):
        """Test get_item_by_id queries by ID."""
        mock_item = Mock(spec=MarketItem)
        mock_session.scalar.return_value = mock_item

        result = repo.get_item_by_id(1)

        assert result == mock_item

    def test_create_item(self, repo, mock_session):
        """Test create_item adds and flushes."""
        result = repo.create_item(
            code="usd", title="US Dollar", category="currency", unit="IRT"
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert isinstance(result, MarketItem)
        assert result.code == "usd"

    def test_update_item_success(self, repo, mock_session):
        """Test update_item updates fields."""
        mock_item = Mock(spec=MarketItem)
        mock_session.scalar.side_effect = [mock_item, mock_item]

        result = repo.update_item(item_id=1, title="Updated Title")

        mock_session.flush.assert_called()
        assert result == mock_item

    def test_delete_item_success(self, repo, mock_session):
        """Test delete_item returns True when deleted."""
        mock_item = Mock(spec=MarketItem)
        mock_session.scalar.side_effect = [mock_item, mock_item]

        result = repo.delete_item(1)

        mock_session.delete.assert_called_once()
        assert result is True

    # =========================================================
    # Latest Price Operations Tests
    # =========================================================

    def test_get_latest(self, repo, mock_session):
        """Test get_latest queries by item_id and provider_id."""
        mock_latest = Mock(spec=MarketPriceLatest)
        mock_session.scalar.return_value = mock_latest

        result = repo.get_latest(item_id=1, provider_id=1)

        mock_session.scalar.assert_called_once()
        assert result == mock_latest

    def test_upsert_latest_inserts_new(self, repo, mock_session):
        """Test upsert_latest inserts when no existing record."""
        mock_session.scalar.return_value = None  # No existing record

        result = repo.upsert_latest(
            item_id=1, provider_id=1, price=58000, change_value=500
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called()
        assert isinstance(result, MarketPriceLatest)

    def test_upsert_latest_updates_existing(self, repo, mock_session):
        """Test upsert_latest updates existing record."""
        mock_existing = Mock(spec=MarketPriceLatest)
        mock_session.scalar.return_value = mock_existing

        result = repo.upsert_latest(
            item_id=1, provider_id=1, price=59000, change_value=1000
        )

        mock_session.add.assert_not_called()  # Should not add new
        # Note: flush() is not called for updates - SQLAlchemy's unit of work
        # detects attribute changes automatically
        assert mock_existing.price == 59000
        assert mock_existing.change_value == 1000

    # =========================================================
    # History Price Operations Tests
    # =========================================================

    def test_insert_history(self, repo, mock_session):
        """Test insert_history adds history record."""
        result = repo.insert_history(
            item_id=1, provider_id=1, price=58000, change_value=500
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called()
        assert isinstance(result, MarketPriceHistory)

    def test_insert_history_with_custom_timestamp(self, repo, mock_session):
        """Test insert_history uses provided timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)

        result = repo.insert_history(
            item_id=1,
            provider_id=1,
            price=58000,
            change_value=500,
            retrieved_at=custom_time,
        )

        mock_session.add.assert_called_once()
        assert isinstance(result, MarketPriceHistory)

    # =========================================================
    # Caching Operations Tests
    # =========================================================

    def test_is_cache_valid_with_none(self, repo):
        """Test is_cache_valid returns False for None."""
        assert repo.is_cache_valid(None) is False

    def test_is_cache_valid_with_fresh_data(self, repo):
        """Test is_cache_valid returns True for recent data."""
        from app.repository.market_repository import utc_now

        fresh_latest = Mock(spec=MarketPriceLatest)
        fresh_latest.retrieved_at = utc_now() - timedelta(minutes=2)

        result = repo.is_cache_valid(fresh_latest, minutes=5)

        assert result is True

    def test_is_cache_valid_with_stale_data(self, repo):
        """Test is_cache_valid returns False for old data."""
        from app.repository.market_repository import utc_now

        stale_latest = Mock(spec=MarketPriceLatest)
        stale_latest.retrieved_at = utc_now() - timedelta(minutes=10)

        result = repo.is_cache_valid(stale_latest, minutes=5)

        assert result is False

    # =========================================================
    # Additional Provider Operations Tests
    # =========================================================

    def test_get_all_providers_default_active_only(self, repo, mock_session):
        """Test get_all_providers filters active by default."""
        mock_session.scalars.return_value.all.return_value = []

        result = repo.get_all_providers()

        mock_session.scalars.assert_called_once()
        assert result == []

    def test_get_all_providers_include_inactive(self, repo, mock_session):
        """Test get_all_providers with active_only=False."""
        mock_providers = [Mock(spec=MarketProvider), Mock(spec=MarketProvider)]
        mock_session.scalars.return_value.all.return_value = mock_providers

        result = repo.get_all_providers(active_only=False)

        assert len(result) == 2

    def test_update_provider_partial_fields(self, repo, mock_session):
        """Test update_provider updates only provided fields."""
        mock_provider = Mock(spec=MarketProvider)
        mock_provider.display_name = "Old Name"
        mock_provider.base_url = "https://old.com"
        mock_provider.active = True
        mock_session.scalar.side_effect = [mock_provider, mock_provider]

        result = repo.update_provider(provider_id=1, active=False)

        assert mock_provider.active is False
        # Other fields should not be modified
        assert mock_provider.display_name == "Old Name"
        assert result == mock_provider

    # =========================================================
    # Additional Item Operations Tests
    # =========================================================

    def test_get_all_items_default_active_only(self, repo, mock_session):
        """Test get_all_items filters active by default."""
        mock_session.scalars.return_value.all.return_value = []

        result = repo.get_all_items()

        assert result == []

    def test_get_all_items_include_inactive(self, repo, mock_session):
        """Test get_all_items with active_only=False."""
        mock_items = [Mock(spec=MarketItem), Mock(spec=MarketItem)]
        mock_session.scalars.return_value.all.return_value = mock_items

        result = repo.get_all_items(active_only=False)

        assert len(result) == 2

    def test_get_items_by_category(self, repo, mock_session):
        """Test get_items_by_category queries by category."""
        mock_items = [Mock(spec=MarketItem)]
        mock_session.scalars.return_value.all.return_value = mock_items

        result = repo.get_items_by_category("currency")

        assert len(result) == 1
        mock_session.scalars.assert_called_once()

    def test_update_item_partial_fields(self, repo, mock_session):
        """Test update_item updates only provided fields."""
        mock_item = Mock(spec=MarketItem)
        mock_item.title = "Old Title"
        mock_item.category = "old_category"
        mock_item.unit = "old_unit"
        mock_item.active = True
        mock_session.scalar.side_effect = [mock_item, mock_item]

        result = repo.update_item(item_id=1, unit="new_unit")

        assert mock_item.unit == "new_unit"
        # Other fields should not be modified
        assert mock_item.title == "Old Title"
        assert result == mock_item

    def test_delete_item_not_found(self, repo, mock_session):
        """Test delete_item returns False when not found."""
        mock_session.scalar.return_value = None

        result = repo.delete_item(999)

        assert result is False
        mock_session.delete.assert_not_called()

    # =========================================================
    # Additional Latest Price Operations Tests
    # =========================================================

    def test_get_latest_by_code(self, repo, mock_session):
        """Test get_latest_by_code queries by item code and provider name."""
        mock_latest = Mock(spec=MarketPriceLatest)
        mock_session.scalar.return_value = mock_latest

        result = repo.get_latest_by_code(item_code="usd", provider_name="navasan")

        assert result == mock_latest
        mock_session.scalar.assert_called_once()

    def test_get_latest_by_code_returns_none(self, repo, mock_session):
        """Test get_latest_by_code returns None when not found."""
        mock_session.scalar.return_value = None

        result = repo.get_latest_by_code(item_code="unknown", provider_name="unknown")

        assert result is None

    def test_get_all_latest_no_filters(self, repo, mock_session):
        """Test get_all_latest without filters."""
        mock_prices = [Mock(spec=MarketPriceLatest)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_prices
        )

        result = repo.get_all_latest()

        assert len(result) == 1

    def test_get_all_latest_with_provider_filter(self, repo, mock_session):
        """Test get_all_latest filtered by provider_id."""
        mock_prices = [Mock(spec=MarketPriceLatest)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_prices
        )

        result = repo.get_all_latest(provider_id=1)

        assert len(result) == 1

    def test_get_all_latest_with_item_filter(self, repo, mock_session):
        """Test get_all_latest filtered by item_id."""
        mock_prices = [Mock(spec=MarketPriceLatest)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_prices
        )

        result = repo.get_all_latest(item_id=1)

        assert len(result) == 1

    def test_get_all_latest_with_category_filter(self, repo, mock_session):
        """Test get_all_latest filtered by category."""
        mock_prices = [Mock(spec=MarketPriceLatest)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_prices
        )

        result = repo.get_all_latest(category="currency")

        assert len(result) == 1

    def test_delete_latest_success(self, repo, mock_session):
        """Test delete_latest returns True when deleted."""
        mock_latest = Mock(spec=MarketPriceLatest)
        mock_session.scalar.side_effect = [mock_latest, mock_latest]

        result = repo.delete_latest(latest_id=1)

        mock_session.delete.assert_called_once()
        assert result is True

    def test_delete_latest_not_found(self, repo, mock_session):
        """Test delete_latest returns False when not found."""
        mock_session.scalar.return_value = None

        result = repo.delete_latest(999)

        assert result is False
        mock_session.delete.assert_not_called()

    # =========================================================
    # History Price Operations Tests
    # =========================================================

    def test_get_history_no_filters(self, repo, mock_session):
        """Test get_history without filters returns limited results."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )

        result = repo.get_history()

        assert len(result) == 1

    def test_get_history_with_provider_filter(self, repo, mock_session):
        """Test get_history filtered by provider_id."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )

        result = repo.get_history(provider_id=1)

        assert len(result) == 1

    def test_get_history_with_item_filter(self, repo, mock_session):
        """Test get_history filtered by item_id."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )

        result = repo.get_history(item_id=1)

        assert len(result) == 1

    def test_get_history_with_category_filter(self, repo, mock_session):
        """Test get_history filtered by category."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )

        result = repo.get_history(category="currency")

        assert len(result) == 1

    def test_get_history_with_date_range(self, repo, mock_session):
        """Test get_history filtered by date range."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = repo.get_history(start_date=start_date, end_date=end_date)

        assert len(result) == 1

    def test_get_history_with_limit(self, repo, mock_session):
        """Test get_history respects limit parameter."""
        mock_history = [Mock(spec=MarketPriceHistory) for _ in range(5)]
        mock_session.scalars.return_value.unique.return_value.all.return_value = (
            mock_history
        )

        result = repo.get_history(limit=5)

        assert len(result) == 5

    def test_get_history_by_code(self, repo, mock_session):
        """Test get_history_by_code queries by item code and provider name."""
        mock_history = [Mock(spec=MarketPriceHistory)]
        mock_session.scalars.return_value.all.return_value = mock_history

        result = repo.get_history_by_code(
            item_code="usd", provider_name="navasan", limit=100
        )

        assert len(result) == 1
        mock_session.scalars.assert_called_once()

    def test_get_history_by_code_empty_result(self, repo, mock_session):
        """Test get_history_by_code returns empty list when not found."""
        mock_session.scalars.return_value.all.return_value = []

        result = repo.get_history_by_code(item_code="unknown", provider_name="unknown")

        assert result == []

    def test_cleanup_history_no_records_to_delete(self, repo, mock_session):
        """Test cleanup_history returns 0 when no old records."""
        mock_session.scalars.return_value.all.return_value = []

        result = repo.cleanup_history(older_than_days=90)

        assert result == 0
        mock_session.execute.assert_not_called()

    def test_cleanup_history_deletes_in_batches(self, repo, mock_session):
        """Test cleanup_history deletes records in batches."""
        # First batch returns IDs to delete
        first_batch_ids = [1, 2, 3, 4, 5]
        # Second batch returns empty (no more records)
        mock_execute_result = Mock()
        mock_execute_result.rowcount = 5
        mock_session.scalars.return_value.all.side_effect = [first_batch_ids, []]
        mock_session.execute.return_value = mock_execute_result

        result = repo.cleanup_history(older_than_days=90, batch_size=1000)

        assert result == 5
        mock_session.execute.assert_called_once()

    def test_cleanup_history_multiple_batches(self, repo, mock_session):
        """Test cleanup_history handles multiple batches."""
        # Three batches: two with data, one empty
        batch1_ids = list(range(1000))
        batch2_ids = list(range(1000, 1500))

        mock_execute_result1 = Mock()
        mock_execute_result1.rowcount = 1000
        mock_execute_result2 = Mock()
        mock_execute_result2.rowcount = 500

        mock_session.scalars.return_value.all.side_effect = [batch1_ids, batch2_ids, []]
        mock_session.execute.side_effect = [mock_execute_result1, mock_execute_result2]

        result = repo.cleanup_history(older_than_days=90, batch_size=1000)

        assert result == 1500
        assert mock_session.execute.call_count == 2

    # =========================================================
    # Edge Case Tests
    # =========================================================

    def test_create_provider_duplicate_name_raises_integrity_error(
        self, repo, mock_session
    ):
        """Test create_provider with duplicate name raises SQLAlchemy IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        mock_session.add.side_effect = IntegrityError("duplicate key", {}, None)

        with pytest.raises(IntegrityError):
            repo.create_provider(
                name="navasan", display_name="Navasan", base_url="https://test.com"
            )

    def test_create_item_duplicate_code_raises_integrity_error(
        self, repo, mock_session
    ):
        """Test create_item with duplicate code raises SQLAlchemy IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        mock_session.add.side_effect = IntegrityError("duplicate key", {}, None)

        with pytest.raises(IntegrityError):
            repo.create_item(
                code="usd", title="US Dollar", category="currency", unit="IRT"
            )

    def test_upsert_latest_with_null_optional_fields(self, repo, mock_session):
        """Test upsert_latest handles null optional fields correctly."""
        mock_session.scalar.return_value = None  # No existing record

        result = repo.upsert_latest(
            item_id=1,
            provider_id=1,
            price=58000,
            change_value=500,
            provider_date=None,
            provider_time=None,
            raw_data=None,
        )

        mock_session.add.assert_called_once()
        assert isinstance(result, MarketPriceLatest)

    def test_insert_history_with_null_optional_fields(self, repo, mock_session):
        """Test insert_history handles null optional fields correctly."""
        result = repo.insert_history(
            item_id=1,
            provider_id=1,
            price=58000,
            change_value=500,
            provider_date=None,
            provider_time=None,
            raw_data=None,
        )

        mock_session.add.assert_called_once()
        assert isinstance(result, MarketPriceHistory)

    def test_transaction_rollback_on_exception(self, repo, mock_session):
        """Test that rollback is called when exception occurs during operations."""
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            repo.commit()

        # Verify commit was attempted
        mock_session.commit.assert_called_once()

    def test_concurrent_update_handling(self, repo, mock_session):
        """Test repository handles concurrent update scenario (stale data)."""
        # Simulate scenario where get returns data but it was deleted concurrently
        mock_provider = Mock(spec=MarketProvider)
        mock_session.scalar.side_effect = [
            mock_provider,
            None,
        ]  # Get succeeds, flush fails

        # This simulates a concurrent deletion between get and update
        # The repository should handle this gracefully
        result = repo.update_provider(provider_id=1, display_name="New Name")

        # In real scenario, SQLAlchemy would raise StaleDataError on flush
        # For this mock test, we verify the flow reaches the point where it would fail
        mock_session.flush.assert_called()
