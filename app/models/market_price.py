from dataclasses import dataclass


@dataclass(slots=True)
class MarketPrice:
    code: str
    title: str
    value: int
    change: int
    update_time: str
    provider: str