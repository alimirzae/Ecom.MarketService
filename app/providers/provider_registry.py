from typing import Dict

from app.providers.base_provider import BaseMarketProvider
from app.providers.navasan_provider import NavasanProvider


class ProviderRegistry:
    """
    Registry of all market providers.

    Responsible only for registering and resolving providers.
    """

    _providers: Dict[str, BaseMarketProvider] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider: BaseMarketProvider,
    ) -> None:

        cls._providers[name.lower()] = provider

    @classmethod
    def get(
        cls,
        name: str,
    ) -> BaseMarketProvider:

        provider = cls._providers.get(name.lower())

        if provider is None:
            raise ValueError(
                f"Provider '{name}' is not registered."
            )

        return provider

    @classmethod
    def exists(
        cls,
        name: str,
    ) -> bool:

        return name.lower() in cls._providers

    @classmethod
    def all(cls):

        return cls._providers.copy()


#
# Register built-in providers
#

ProviderRegistry.register(
    "navasan",
    NavasanProvider(),
)