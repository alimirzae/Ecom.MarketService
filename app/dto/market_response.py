from dataclasses import dataclass

from app.dto.market_price_dto import MarketPriceDto


@dataclass(slots=True)
class MarketResponse:

    success: bool

    items: list[MarketPriceDto]