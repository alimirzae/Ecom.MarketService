from dataclasses import dataclass


@dataclass(slots=True)
class MarketRequest:

    codes: list[str]

    provider: str = "navasan"

    force: bool = False