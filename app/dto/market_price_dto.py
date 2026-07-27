from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MarketPriceDto:

    code: str

    title: str

    price: int

    change: int

    provider: str

    provider_time: str

    retrieved_at: datetime