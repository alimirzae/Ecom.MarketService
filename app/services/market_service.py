"""
Business Service Layer for Market Data.

This module contains ALL business logic for market price operations.

Responsibilities:
- Price refresh orchestration
- Cache management
- Provider selection
- Data validation
- Transaction coordination

MUST NOT:
- Access SQLAlchemy directly
- Parse HTML
- Make HTTP requests
- Know about FastAPI
"""

from datetime import datetime, timezone
from typing import TypedDict

from loguru import logger

from app.dto.market_price_dto import MarketPriceDto
from app.dto.provider_result import ProviderResult
from app.providers.provider_registry import ProviderRegistry
from app.repository.market_repository import MarketRepository


class LatestPriceEntry(TypedDict):
    """Type hint for latest price lookup results."""

    item_id: int
    item_code: str
    title: str


class MarketService:
    """
    Business service for market price operations.

    This service orchestrates price retrieval, caching, and storage.
    It coordinates between repositories and providers without knowing
    implementation details of either.
    """

    def __init__(self, repository: MarketRepository):
        """
        Initialize MarketService.

        Args:
            repository: Market repository instance for database operations.
        """
        self.repository = repository
        self._default_expiration_minutes = 5

    # =========================================================
    # Public API
    # =========================================================

    async def get_latest_prices(
        self,
        codes: list[str] | None = None,
        provider_name: str = "navasan",
        force: bool = False,
        category: str | None = None,
    ) -> list[MarketPriceDto]:
        """
        Get latest market prices with automatic refresh if needed.

        Business Logic:
        1. Validate provider exists
        2. Validate/filter requested codes
        3. Check cache expiration
        4. Refresh from provider if cache miss/expired/force
        5. Store latest and history
        6. Return DTOs

        Args:
            codes: List of item codes to retrieve. None = all active items.
            provider_name: Name of the provider to use.
            force: If True, always refresh from provider ignoring cache.
            category: Optional category filter (used when codes is None).

        Returns:
            List of MarketPriceDto with latest prices.

        Raises:
            ValueError: If provider is not registered.
            RuntimeError: If provider fails to return data.
        """
        logger.info(f"Getting latest prices: provider={provider_name}, force={force}")

        # Step 1: Validate provider
        provider = self._validate_provider(provider_name)

        # Step 2: Get target items
        items_to_fetch = self._get_target_items(codes, category)

        if not items_to_fetch:
            logger.warning("No items to fetch")
            return []

        # Step 3: Check cache
        if not force and self._can_use_cache(items_to_fetch, provider_name):
            logger.info("Using cached prices")
            return self._build_response_from_cache(items_to_fetch, provider_name)

        # Step 4: Refresh from provider
        logger.info("Refreshing prices from provider")
        codes_to_fetch = [item["item_code"] for item in items_to_fetch]

        try:
            provider_results = await self._refresh_from_provider(
                codes_to_fetch, provider_name
            )
        except Exception as e:
            logger.error(f"Provider refresh failed: {e}")
            raise

        # Step 5: Store results
        retrieved_at = datetime.now(timezone.utc)

        try:
            self.repository.begin_transaction()

            # Build item_id lookup
            item_id_map = {item["item_code"]: item["item_id"] for item in items_to_fetch}

            # Store latest prices
            self._store_latest_prices(
                item_id_map=item_id_map,
                provider_name=provider_name,
                results=provider_results,
            )

            # Store history
            self._store_history(
                item_id_map=item_id_map,
                provider_name=provider_name,
                results=provider_results,
                retrieved_at=retrieved_at,
            )

            self.repository.commit()
            logger.info(f"Successfully stored {len(provider_results)} prices")

        except Exception as e:
            self.repository.rollback()
            logger.error(f"Failed to store prices: {e}")
            raise

        # Step 6: Build and return response
        return self._build_response(provider_results, provider_name, retrieved_at)

    def get_price_history(
        self,
        codes: list[str] | None = None,
        provider_name: str | None = None,
        limit: int = 100,
        category: str | None = None,
    ) -> list[MarketPriceDto]:
        """
        Get historical price data.

        Args:
            codes: List of item codes. None = all items.
            provider_name: Filter by provider. None = all providers.
            limit: Maximum number of records per item.
            category: Optional category filter.

        Returns:
            List of MarketPriceDto with historical prices.
        """
        logger.info(f"Getting price history: limit={limit}")

        # Get target items
        items = self._get_target_items(codes, category)

        if not items:
            return []

        results: list[MarketPriceDto] = []

        for item in items:
            if provider_name:
                # Get history for specific provider
                history_records = self.repository.get_history_by_code(
                    item_code=item["item_code"],
                    provider_name=provider_name,
                    limit=limit,
                )
            else:
                # Get history from all providers
                history_records = self.repository.get_history(
                    item_id=item["item_id"],
                    limit=limit,
                )

            for record in history_records:
                dto = MarketPriceDto(
                    code=item["item_code"],
                    title=item["title"],
                    price=record.price,
                    change=record.change_value,
                    provider=record.provider.name,
                    provider_time=record.provider_time or "",
                    retrieved_at=record.retrieved_at,
                )
                results.append(dto)

        return results

    async def force_refresh(
        self,
        codes: list[str] | None = None,
        provider_name: str = "navasan",
        category: str | None = None,
    ) -> list[MarketPriceDto]:
        """
        Force refresh prices from provider, ignoring cache.

        Convenience wrapper around get_latest_prices(force=True).

        Args:
            codes: List of item codes. None = all active items.
            provider_name: Name of the provider.
            category: Optional category filter.

        Returns:
            List of MarketPriceDto with refreshed prices.
        """
        return await self.get_latest_prices(
            codes=codes,
            provider_name=provider_name,
            force=True,
            category=category,
        )

    async def refresh_if_expired(
        self,
        codes: list[str] | None = None,
        provider_name: str = "navasan",
        expiration_minutes: int | None = None,
        category: str | None = None,
    ) -> list[MarketPriceDto]:
        """
        Refresh prices only if cache has expired.

        Args:
            codes: List of item codes. None = all active items.
            provider_name: Name of the provider.
            expiration_minutes: Custom expiration time. Uses default if None.
            category: Optional category filter.

        Returns:
            List of MarketPriceDto with prices (cached or refreshed).
        """
        if expiration_minutes is not None:
            old_default = self._default_expiration_minutes
            self._default_expiration_minutes = expiration_minutes
            try:
                return await self.get_latest_prices(
                    codes=codes,
                    provider_name=provider_name,
                    force=False,
                    category=category,
                )
            finally:
                self._default_expiration_minutes = old_default

        return await self.get_latest_prices(
            codes=codes,
            provider_name=provider_name,
            force=False,
            category=category,
        )

    # =========================================================
    # Private Methods - Cache Management
    # =========================================================

    def _can_use_cache(
        self,
        items: list[LatestPriceEntry],
        provider_name: str,
    ) -> bool:
        """
        Check if cached prices are still valid for all requested items.

        Args:
            items: List of items to check.
            provider_name: Name of the provider.

        Returns:
            True if all items have valid cached prices.
        """
        # Get provider ID
        provider = self.repository.get_provider(provider_name)
        if provider is None:
            return False

        provider_id = provider.id

        # Check each item's cache
        for item in items:
            latest = self.repository.get_latest(
                item_id=item["item_id"],
                provider_id=provider_id,
            )

            if not self.repository.is_cache_valid(
                latest, self._default_expiration_minutes
            ):
                return False

        return True

    def _build_response_from_cache(
        self,
        items: list[LatestPriceEntry],
        provider_name: str,
    ) -> list[MarketPriceDto]:
        """
        Build response DTOs from cached data.

        Args:
            items: List of items to build response for.
            provider_name: Name of the provider.

        Returns:
            List of MarketPriceDto from cache.
        """
        provider = self.repository.get_provider(provider_name)
        if provider is None:
            return []

        provider_id = provider.id
        results: list[MarketPriceDto] = []

        for item in items:
            latest = self.repository.get_latest(
                item_id=item["item_id"],
                provider_id=provider_id,
            )

            if latest is not None:
                dto = MarketPriceDto(
                    code=item["item_code"],
                    title=item["title"],
                    price=latest.price,
                    change=latest.change_value,
                    provider=provider_name,
                    provider_time=latest.provider_time or "",
                    retrieved_at=latest.retrieved_at,
                )
                results.append(dto)

        return results

    # =========================================================
    # Private Methods - Provider Interaction
    # =========================================================

    def _validate_provider(self, provider_name: str) -> object:
        """
        Validate that a provider is registered.

        Args:
            provider_name: Name of the provider to validate.

        Returns:
            Provider instance.

        Raises:
            ValueError: If provider is not registered.
        """
        if not ProviderRegistry.exists(provider_name):
            raise ValueError(f"Provider '{provider_name}' is not registered.")

        return ProviderRegistry.get(provider_name)

    async def _refresh_from_provider(
        self,
        codes: list[str],
        provider_name: str,
    ) -> list[ProviderResult]:
        """
        Fetch latest prices from external provider.

        Args:
            codes: List of item codes to fetch.
            provider_name: Name of the provider.

        Returns:
            List of ProviderResult from provider.

        Raises:
            RuntimeError: If provider returns empty results.
        """
        
        
        provider = ProviderRegistry.get(provider_name)

        # Call provider method (all providers are sync in this implementation)
        try:
            results = await provider.get_latest_prices(codes)
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            raise RuntimeError(f"Provider '{provider_name}' failed: {e}") from e

        if not results:
            logger.warning(f"Provider {provider_name} returned no data")
            raise RuntimeError(f"Provider '{provider_name}' returned no data")

        return results

    # =========================================================
    # Private Methods - Storage Operations
    # =========================================================

    def _store_latest_prices(
        self,
        item_id_map: dict[str, int],
        provider_name: str,
        results: list[ProviderResult],
    ) -> None:
        """
        Store latest prices using upsert operation.

        Args:
            item_id_map: Mapping of item codes to IDs.
            provider_name: Name of the provider.
            results: List of ProviderResult to store.
        """
        provider = self.repository.get_provider(provider_name)
        if provider is None:
            raise ValueError(f"Provider '{provider_name}' not found.")

        provider_id = provider.id

        for result in results:
            if result.code not in item_id_map:
                logger.warning(f"Unknown item code: {result.code}")
                continue

            item_id = item_id_map[result.code]

            self.repository.upsert_latest(
                item_id=item_id,
                provider_id=provider_id,
                price=result.price,
                change_value=result.change,
                provider_time=result.provider_time,
                raw_data={"title": result.title},
            )

    def _store_history(
        self,
        item_id_map: dict[str, int],
        provider_name: str,
        results: list[ProviderResult],
        retrieved_at: datetime,
    ) -> None:
        """
        Store historical price records.

        Args:
            item_id_map: Mapping of item codes to IDs.
            provider_name: Name of the provider.
            results: List of ProviderResult to store.
            retrieved_at: Timestamp for the records.
        """
        provider = self.repository.get_provider(provider_name)
        if provider is None:
            raise ValueError(f"Provider '{provider_name}' not found.")

        provider_id = provider.id

        for result in results:
            if result.code not in item_id_map:
                continue

            item_id = item_id_map[result.code]

            self.repository.insert_history(
                item_id=item_id,
                provider_id=provider_id,
                price=result.price,
                change_value=result.change,
                provider_time=result.provider_time,
                raw_data={"title": result.title},
                retrieved_at=retrieved_at,
            )

    # =========================================================
    # Private Methods - Helper Functions
    # =========================================================

    def _get_target_items(
        self,
        codes: list[str] | None = None,
        category: str | None = None,
    ) -> list[LatestPriceEntry]:
        """
        Get list of items to fetch based on codes or category.

        Args:
            codes: Specific item codes. None = use category or all active.
            category: Category filter. Used when codes is None.

        Returns:
            List of LatestPriceEntry with item information.
        """
        if codes is not None:
            # Fetch specific codes
            items: list[LatestPriceEntry] = []
            for code in codes:
                item = self.repository.get_item(code)
                if item is not None:
                    items.append(
                        LatestPriceEntry(
                            item_id=item.id,
                            item_code=item.code,
                            title=item.title
                        )
                    )
                else:
                    logger.warning(f"Item code not found: {code}")
            return items

        elif category is not None:
            # Fetch by category
            items = self.repository.get_items_by_category(category)
            return [
                LatestPriceEntry(
                    item_id=item.id,
                    item_code=item.code,
                    title=item.title 
                )
                for item in items
            ]

        else:
            # Fetch all active items
            items = self.repository.get_all_items(active_only=True)
            return [
                LatestPriceEntry(
                    item_id=item.id,
                    item_code=item.code,
                    title=item.title,
                )
                for item in items
            ]

    def _build_response(
        self,
        results: list[ProviderResult],
        provider_name: str,
        retrieved_at: datetime,
    ) -> list[MarketPriceDto]:
        """
        Build response DTOs from provider results.

        Args:
            results: List of ProviderResult from provider.
            provider_name: Name of the provider.
            retrieved_at: Timestamp when data was retrieved.

        Returns:
            List of MarketPriceDto.
        """
        return [
            MarketPriceDto(
                code=result.code,
                title=result.title,
                price=result.price,
                change=result.change,
                provider=provider_name,
                provider_time=result.provider_time,
                retrieved_at=retrieved_at,
            )
            for result in results
        ]
