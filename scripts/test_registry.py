from app.providers.provider_registry import ProviderRegistry

provider = ProviderRegistry.get("navasan")

print(provider)