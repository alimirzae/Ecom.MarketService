from sqlalchemy import Index

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.entities.base_price import BasePriceMixin


class MarketPriceHistory(Base, BasePriceMixin):
    __tablename__ = "market_price_history"

    __table_args__ = (
        Index(
            "ix_history_item_provider_time",
            "item_id",
            "provider_id",
            "retrieved_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    item = relationship(
        "MarketItem",
        back_populates="history_prices",
    )

    provider = relationship(
        "MarketProvider",
        back_populates="history_prices",
    )