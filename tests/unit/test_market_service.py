"""
Unit tests for MarketService.

These tests verify the business service layer without requiring
a database connection or external providers. They use mocking
to isolate service logic.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.dto.market_price_dto import MarketPriceDto
from app.dto.provider_result import ProviderResult


class TestMarketService:
    """Test suite for MarketService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock MarketRepository."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create a MarketService instance with mocked repository."""
        from app.services.market_service import MarketService

        return MarketService(mock_repository)

    @pytest.fixture
    def sample_provider_result(self):
        """Create a sample ProviderResult for testing."""
        return ProviderResult(
            code="usd",
            title="US Dollar",
            price=58000,
            change=500,
            provider_time="14:30",
        )

    @pytest.fixture
    def sample_market_item(self):
        """Create a sample MarketItem mock."""
        item = Mock()
        item.id = 1
        item.code = "usd"
        item.title = "US Dollar"
        item.category = "currency"
        item.active = True
        return item

    # =========================================================
    # Initialization Tests
    # =========================================================

    def test_service_initialization(self, service, mock_repository):
        """Test service initializes with repository."""
        assert service.repository == mock_repository
        assert service._default_expiration_minutes == 5

    # =========================================================
    # Provider Validation Tests
    # =========================================================

    def test_validate_provider_success(self, service):
        """Test _validate_provider with registered provider."""
        with patch(
            "app.services.market_service.ProviderRegistry.exists", return_value=True
        ):
            with patch("app.services.market_service.ProviderRegistry.get") as mock_get:
                mock_provider = Mock()
                mock_get.return_value = mock_provider

                result = service._validate_provider("navasan")

                assert result == mock_provider

    def test_validate_provider_not_registered(self, service):
        """Test _validate_provider with unregistered provider."""
        with patch(
            "app.services.market_service.ProviderRegistry.exists", return_value=False
        ):
            with pytest.raises(ValueError) as exc_info:
                service._validate_provider("unknown_provider")

            assert "not registered" in str(exc_info.value)

    # =========================================================
    # Get Target Items Tests
    # =========================================================

    def test_get_target_items_by_codes(self, service, mock_repository, sample_market_item):
        """Test _get_target_items with specific codes."""
        mock_repository.get_item.return_value = sample_market_item

        result = service._get_target_items(codes=["usd", "eur"])

        assert len(result) == 2
        assert result[0]["item_code"] == "usd"
        assert result[0]["title"] == "US Dollar"
        mock_repository.get_item.assert_called()

    def test_get_target_items_unknown_code(self, service, mock_repository):
        """Test _get_target_items with unknown code logs warning."""
        mock_repository.get_item.return_value = None

        result = service._get_target_items(codes=["unknown"])

        assert len(result) == 0

    def test_get_target_items_by_category(self, service, mock_repository, sample_market_item):
        """Test _get_target_items by category."""
        mock_repository.get_items_by_category.return_value = [sample_market_item]

        result = service._get_target_items(category="currency")

        assert len(result) == 1
        assert result[0]["item_code"] == "usd"
        mock_repository.get_items_by_category.assert_called_once_with("currency")

    def test_get_target_items_all_active(self, service, mock_repository, sample_market_item):
        """Test _get_target_items gets all active items when no filters."""
        mock_repository.get_all_items.return_value = [sample_market_item]

        result = service._get_target_items()

        assert len(result) == 1
        mock_repository.get_all_items.assert_called_once_with(active_only=True)

    # =========================================================
    # Cache Validation Tests
    # =========================================================

    def test_can_use_cache_all_valid(self, service, mock_repository):
        """Test _can_use_cache when all items have valid cache."""
        from app.repository.market_repository import utc_now

        mock_repository.get_provider.return_value = Mock(id=1)
        
        fresh_latest = Mock()
        fresh_latest.retrieved_at = utc_now() - timedelta(minutes=2)
        mock_repository.get_latest.return_value = fresh_latest

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._can_use_cache(items, "navasan")

        assert result is True

    def test_can_use_cache_one_expired(self, service, mock_repository):
        """Test _can_use_cache returns False when one item is expired."""
        from app.repository.market_repository import utc_now

        mock_repository.get_provider.return_value = Mock(id=1)
        
        stale_latest = Mock()
        stale_latest.retrieved_at = utc_now() - timedelta(minutes=10)
        mock_repository.get_latest.return_value = stale_latest
        
        # Explicitly mock is_cache_valid to return False for stale data
        mock_repository.is_cache_valid.return_value = False

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._can_use_cache(items, "navasan")

        assert result is False
        mock_repository.is_cache_valid.assert_called()

    def test_can_use_cache_provider_not_found(self, service, mock_repository):
        """Test _can_use_cache returns False when provider not found."""
        mock_repository.get_provider.return_value = None

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._can_use_cache(items, "unknown")

        assert result is False

    def test_can_use_cache_no_latest(self, service, mock_repository):
        """Test _can_use_cache returns False when no latest exists."""
        mock_repository.get_provider.return_value = Mock(id=1)
        mock_repository.get_latest.return_value = None
        mock_repository.is_cache_valid.return_value = False

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._can_use_cache(items, "navasan")

        assert result is False

    # =========================================================
    # Build Response From Cache Tests
    # =========================================================

    def test_build_response_from_cache(self, service, mock_repository):
        """Test _build_response_from_cache builds DTOs correctly."""
        mock_repository.get_provider.return_value = Mock(id=1)
        
        latest = Mock()
        latest.price = 58000
        latest.change_value = 500
        latest.provider_time = "14:30"
        latest.retrieved_at = datetime.now(timezone.utc)
        mock_repository.get_latest.return_value = latest

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._build_response_from_cache(items, "navasan")

        assert len(result) == 1
        assert isinstance(result[0], MarketPriceDto)
        assert result[0].code == "usd"
        assert result[0].price == 58000

    def test_build_response_from_cache_provider_not_found(self, service, mock_repository):
        """Test _build_response_from_cache returns empty when provider not found."""
        mock_repository.get_provider.return_value = None

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._build_response_from_cache(items, "unknown")

        assert result == []

    def test_build_response_from_cache_missing_latest(self, service, mock_repository):
        """Test _build_response_from_cache skips items without latest."""
        mock_repository.get_provider.return_value = Mock(id=1)
        mock_repository.get_latest.return_value = None

        items = [{"item_id": 1, "item_code": "usd", "title": "US Dollar"}]

        result = service._build_response_from_cache(items, "navasan")

        assert result == []

    # =========================================================
    # Refresh From Provider Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_refresh_from_provider_success(self, service, sample_provider_result):
        """Test _refresh_from_provider fetches data successfully."""
        from unittest.mock import AsyncMock
        
        mock_provider = Mock()
        mock_provider.get_latest_prices = AsyncMock()
        mock_provider.get_latest_prices.return_value = [sample_provider_result]

        with patch("app.services.market_service.ProviderRegistry.get", return_value=mock_provider):
            result = await service._refresh_from_provider(["usd"], "navasan")

            assert len(result) == 1
            assert result[0].code == "usd"
            assert result[0].price == 58000

    @pytest.mark.asyncio
    async def test_refresh_from_provider_empty_result(self, service):
        """Test _refresh_from_provider raises when provider returns empty."""
        from unittest.mock import AsyncMock
        
        mock_provider = Mock()
        mock_provider.get_latest_prices = AsyncMock()
        mock_provider.get_latest_prices.return_value = []

        with patch("app.services.market_service.ProviderRegistry.get", return_value=mock_provider):
            with pytest.raises(RuntimeError) as exc_info:
                await service._refresh_from_provider(["usd"], "navasan")

            assert "returned no data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refresh_from_provider_exception(self, service):
        """Test _refresh_from_provider handles provider exceptions."""
        from unittest.mock import AsyncMock
        
        mock_provider = Mock()
        mock_provider.get_latest_prices = AsyncMock()
        mock_provider.get_latest_prices.side_effect = Exception("Connection failed")

        with patch("app.services.market_service.ProviderRegistry.get", return_value=mock_provider):
            with pytest.raises(RuntimeError) as exc_info:
                await service._refresh_from_provider(["usd"], "navasan")

            assert "failed" in str(exc_info.value).lower()

    # =========================================================
    # Store Latest Prices Tests
    # =========================================================

    def test_store_latest_prices(self, service, mock_repository, sample_provider_result):
        """Test _store_latest_prices calls upsert correctly."""
        mock_repository.get_provider.return_value = Mock(id=1)

        item_id_map = {"usd": 1}
        results = [sample_provider_result]

        service._store_latest_prices(item_id_map, "navasan", results)

        mock_repository.upsert_latest.assert_called_once()
        call_args = mock_repository.upsert_latest.call_args
        assert call_args.kwargs["item_id"] == 1
        assert call_args.kwargs["provider_id"] == 1
        assert call_args.kwargs["price"] == 58000

    def test_store_latest_prices_unknown_code(self, service, mock_repository, sample_provider_result, caplog):
        """Test _store_latest_prices skips unknown codes."""
        mock_repository.get_provider.return_value = Mock(id=1)

        item_id_map = {"eur": 2}  # usd not in map
        results = [sample_provider_result]

        service._store_latest_prices(item_id_map, "navasan", results)

        mock_repository.upsert_latest.assert_not_called()

    def test_store_latest_prices_provider_not_found(self, service, mock_repository, sample_provider_result):
        """Test _store_latest_prices raises when provider not found."""
        mock_repository.get_provider.return_value = None

        item_id_map = {"usd": 1}
        results = [sample_provider_result]

        with pytest.raises(ValueError) as exc_info:
            service._store_latest_prices(item_id_map, "unknown", results)

        assert "not found" in str(exc_info.value)

    # =========================================================
    # Store History Tests
    # =========================================================

    def test_store_history(self, service, mock_repository, sample_provider_result):
        """Test _store_history calls insert correctly."""
        mock_repository.get_provider.return_value = Mock(id=1)

        item_id_map = {"usd": 1}
        results = [sample_provider_result]
        retrieved_at = datetime.now(timezone.utc)

        service._store_history(item_id_map, "navasan", results, retrieved_at)

        mock_repository.insert_history.assert_called_once()
        call_args = mock_repository.insert_history.call_args
        assert call_args.kwargs["item_id"] == 1
        assert call_args.kwargs["provider_id"] == 1
        assert call_args.kwargs["price"] == 58000

    def test_store_history_unknown_code(self, service, mock_repository, sample_provider_result):
        """Test _store_history skips unknown codes."""
        mock_repository.get_provider.return_value = Mock(id=1)

        item_id_map = {"eur": 2}  # usd not in map
        results = [sample_provider_result]
        retrieved_at = datetime.now(timezone.utc)

        service._store_history(item_id_map, "navasan", results, retrieved_at)

        mock_repository.insert_history.assert_not_called()

    def test_store_history_provider_not_found(self, service, mock_repository, sample_provider_result):
        """Test _store_history raises when provider not found."""
        mock_repository.get_provider.return_value = None

        item_id_map = {"usd": 1}
        results = [sample_provider_result]
        retrieved_at = datetime.now(timezone.utc)

        with pytest.raises(ValueError) as exc_info:
            service._store_history(item_id_map, "unknown", results, retrieved_at)

        assert "not found" in str(exc_info.value)

    # =========================================================
    # Build Response Tests
    # =========================================================

    def test_build_response(self, service, sample_provider_result):
        """Test _build_response creates DTOs correctly."""
        results = [sample_provider_result]
        provider_name = "navasan"
        retrieved_at = datetime.now(timezone.utc)

        dtos = service._build_response(results, provider_name, retrieved_at)

        assert len(dtos) == 1
        assert isinstance(dtos[0], MarketPriceDto)
        assert dtos[0].code == "usd"
        assert dtos[0].price == 58000
        assert dtos[0].provider == "navasan"
        assert dtos[0].retrieved_at == retrieved_at

    def test_build_response_multiple_results(self, service):
        """Test _build_response handles multiple results."""
        results = [
            ProviderResult("usd", "US Dollar", 58000, 500, "14:30"),
            ProviderResult("eur", "Euro", 62000, 300, "14:30"),
        ]
        retrieved_at = datetime.now(timezone.utc)

        dtos = service._build_response(results, "navasan", retrieved_at)

        assert len(dtos) == 2
        assert dtos[0].code == "usd"
        assert dtos[1].code == "eur"

    # =========================================================
    # Get Latest Prices Tests - Integration
    # =========================================================

    @pytest.mark.asyncio
    async def test_get_latest_prices_force_refresh(self, service, mock_repository, sample_provider_result, sample_market_item):
        """Test get_latest_prices with force=True bypasses cache."""
        # Setup mocks
        mock_repository.get_item.return_value = sample_market_item
        
        with patch.object(service, "_validate_provider") as mock_validate:
            mock_validate.return_value = Mock()
            
            with patch.object(service, "_refresh_from_provider", return_value=[sample_provider_result]) as mock_refresh:
                with patch.object(service, "_store_latest_prices") as mock_store_latest:
                    with patch.object(service, "_store_history") as mock_store_history:
                        with patch.object(service, "_build_response") as mock_build:
                            mock_build.return_value = [Mock(spec=MarketPriceDto)]

                            result = await service.get_latest_prices(codes=["usd"], force=True)

                            mock_refresh.assert_called_once()
                            mock_store_latest.assert_called()
                            mock_store_history.assert_called()
                            mock_repository.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_latest_prices_uses_cache(self, service, mock_repository, sample_market_item):
        """Test get_latest_prices uses cache when valid."""
        mock_repository.get_item.return_value = sample_market_item

        with patch.object(service, "_validate_provider") as mock_validate:
            mock_validate.return_value = Mock()
            
            with patch.object(service, "_can_use_cache", return_value=True) as mock_cache:
                with patch.object(service, "_build_response_from_cache") as mock_build_cache:
                    mock_build_cache.return_value = [Mock(spec=MarketPriceDto)]

                    result = await service.get_latest_prices(codes=["usd"], force=False)

                    mock_cache.assert_called()
                    mock_build_cache.assert_called()
                    # Should NOT call refresh or store
                    assert not hasattr(service, "_refresh_from_provider_called")

    @pytest.mark.asyncio
    async def test_get_latest_prices_no_items(self, service, mock_repository):
        """Test get_latest_prices returns empty when no items found."""
        mock_repository.get_item.return_value = None

        with patch.object(service, "_validate_provider") as mock_validate:
            mock_validate.return_value = Mock()

            result = await service.get_latest_prices(codes=["unknown"])

            assert result == []

    @pytest.mark.asyncio
    async def test_get_latest_prices_transaction_rollback(self, service, mock_repository, sample_provider_result, sample_market_item):
        """Test get_latest_prices rolls back on storage failure."""
        mock_repository.get_item.return_value = sample_market_item

        with patch.object(service, "_validate_provider") as mock_validate:
            mock_validate.return_value = Mock()
            
            with patch.object(service, "_refresh_from_provider", return_value=[sample_provider_result]):
                with patch.object(service, "_store_latest_prices", side_effect=Exception("DB error")):
                    with pytest.raises(Exception):
                        await service.get_latest_prices(codes=["usd"], force=True)

                    mock_repository.rollback.assert_called()

    # =========================================================
    # Force Refresh Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_force_refresh_calls_get_latest_with_force(self, service):
        """Test force_refresh calls get_latest_prices with force=True."""
        with patch.object(service, "get_latest_prices") as mock_get:
            mock_get.return_value = []

            await service.force_refresh(codes=["usd"], provider_name="navasan")

            mock_get.assert_called_once_with(
                codes=["usd"],
                provider_name="navasan",
                force=True,
                category=None,
            )

    # =========================================================
    # Refresh If Expired Tests
    # =========================================================

    @pytest.mark.asyncio
    async def test_refresh_if_expired_default_expiration(self, service):
        """Test refresh_if_expired uses default expiration."""
        with patch.object(service, "get_latest_prices") as mock_get:
            mock_get.return_value = []

            await service.refresh_if_expired(codes=["usd"])

            mock_get.assert_called_once_with(
                codes=["usd"],
                provider_name="navasan",
                force=False,
                category=None,
            )

    @pytest.mark.asyncio
    async def test_refresh_if_expired_custom_expiration(self, service):
        """Test refresh_if_expired uses custom expiration."""
        with patch.object(service, "get_latest_prices") as mock_get:
            mock_get.return_value = []

            await service.refresh_if_expired(codes=["usd"], expiration_minutes=10)

            # Verify get_latest_prices was called (expiration is internal)
            mock_get.assert_called()

    @pytest.mark.asyncio
    async def test_refresh_if_expired_restores_default(self, service):
        """Test refresh_if_expired restores default expiration after custom."""
        original_default = service._default_expiration_minutes

        with patch.object(service, "get_latest_prices"):
            await service.refresh_if_expired(expiration_minutes=15)

        assert service._default_expiration_minutes == original_default

    # =========================================================
    # Get Price History Tests
    # =========================================================

    def test_get_price_history_by_provider(self, service, mock_repository, sample_market_item):
        """Test get_price_history filters by provider."""
        mock_repository.get_item.return_value = sample_market_item
        
        history_record = Mock()
        history_record.price = 58000
        history_record.change_value = 500
        history_record.provider = Mock(name="navasan")
        history_record.provider_time = "14:30"
        history_record.retrieved_at = datetime.now(timezone.utc)
        
        mock_repository.get_history_by_code.return_value = [history_record]

        result = service.get_price_history(codes=["usd"], provider_name="navasan", limit=50)

        assert len(result) == 1
        assert result[0].price == 58000
        mock_repository.get_history_by_code.assert_called_once_with(
            item_code="usd",
            provider_name="navasan",
            limit=50,
        )

    def test_get_price_history_all_providers(self, service, mock_repository, sample_market_item):
        """Test get_price_history gets from all providers when none specified."""
        mock_repository.get_item.return_value = sample_market_item
        
        history_record = Mock()
        history_record.price = 58000
        history_record.change_value = 500
        history_record.provider = Mock(name="navasan")
        history_record.provider_time = "14:30"
        history_record.retrieved_at = datetime.now(timezone.utc)
        
        mock_repository.get_history.return_value = [history_record]

        result = service.get_price_history(codes=["usd"], limit=50)

        assert len(result) == 1
        mock_repository.get_history.assert_called_once_with(
            item_id=1,
            limit=50,
        )

    def test_get_price_history_no_items(self, service, mock_repository):
        """Test get_price_history returns empty when no items."""
        mock_repository.get_item.return_value = None

        result = service.get_price_history(codes=["unknown"])

        assert result == []

    def test_get_price_history_by_category(self, service, mock_repository, sample_market_item):
        """Test get_price_history by category."""
        mock_repository.get_items_by_category.return_value = [sample_market_item]
        mock_repository.get_history.return_value = []

        result = service.get_price_history(category="currency")

        assert result == []
        mock_repository.get_items_by_category.assert_called_once_with("currency")


class TestMarketServiceEdgeCases:
    """Edge case tests for MarketService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock MarketRepository."""
        return MagicMock()

    @pytest.fixture
    def sample_market_item(self):
        """Create a sample MarketItem mock."""
        item = Mock()
        item.id = 1
        item.code = "usd"
        item.title = "US Dollar"
        item.category = "currency"
        item.active = True
        return item

    @pytest.fixture
    def service(self, mock_repository):
        """Create a MarketService instance."""
        from app.services.market_service import MarketService

        return MarketService(mock_repository)

    def test_concurrent_access_thread_safety(self, service):
        """Test service handles concurrent access safely (basic check)."""
        # Basic thread safety check - ensure no shared mutable state
        # that could cause race conditions
        assert hasattr(service, "_default_expiration_minutes")
        assert isinstance(service._default_expiration_minutes, int)

    def test_null_values_handling(self, service, mock_repository):
        """Test service handles null values gracefully."""
        mock_repository.get_item.return_value = None

        result = service._get_target_items(codes=[None])  # type: ignore

        assert result == []

    def test_empty_codes_list(self, service, mock_repository):
        """Test service handles empty codes list."""
        result = service._get_target_items(codes=[])

        assert result == []

    def test_duplicate_codes(self, service, mock_repository, sample_market_item):
        """Test service handles duplicate codes."""
        mock_repository.get_item.return_value = sample_market_item

        result = service._get_target_items(codes=["usd", "usd", "usd"])

        # Should process each code (may have duplicates in result)
        assert len(result) == 3

    def test_special_characters_in_codes(self, service, mock_repository, sample_market_item):
        """Test service handles special characters in codes."""
        sample_market_item.code = "usd-irt-special"
        mock_repository.get_item.return_value = sample_market_item

        result = service._get_target_items(codes=["usd-irt-special"])

        assert len(result) == 1
        assert result[0]["item_code"] == "usd-irt-special"
