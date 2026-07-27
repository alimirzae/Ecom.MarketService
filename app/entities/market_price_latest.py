from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.entities.base_price import BasePriceMixin


class MarketPriceLatest(Base, BasePriceMixin):
    __tablename__ = "market_price_latest"

    __table_args__ = (
        UniqueConstraint(
            "item_id",
            "provider_id",
            name="uq_latest_item_provider",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    item = relationship(
        "MarketItem",
        back_populates="latest_prices",
    )

    provider = relationship(
        "MarketProvider",
        back_populates="latest_prices",
    )