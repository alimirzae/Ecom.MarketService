from abc import ABC
from abc import abstractmethod

from app.dto.provider_result import ProviderResult


class BaseMarketProvider(ABC):
    """
    Base interface for all market providers.
    """

    @abstractmethod
    async def get_latest_prices(
        self,
        codes: list[str],
    ) -> list[ProviderResult]:
        """
        Fetch latest prices from remote provider.
        """
        raise NotImplementedError