from dataclasses import dataclass


@dataclass(slots=True)
class ProviderResult:

    code: str

    title: str

    price: int

    change: int

    provider_time: str