from app.providers.navasan_provider import NavasanProvider


class ProviderFactory:

    _providers = {
        "navasan": NavasanProvider(),
    }

    @classmethod
    def get(cls, name: str):

        return cls._providers[name]