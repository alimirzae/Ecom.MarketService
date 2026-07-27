from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.market_provider import MarketProvider
from app.entities.market_item import MarketItem
from app.entities.market_price_latest import MarketPriceLatest
from app.entities.market_price_history import MarketPriceHistory


class MarketRepository:

    def __init__(self, db: Session):

        self.db = db

    # ---------------------------------------------------------
    # Provider
    # ---------------------------------------------------------

    def get_provider(
        self,
        name: str,
    ) -> MarketProvider | None:

        stmt = (
            select(MarketProvider)
            .where(MarketProvider.name == name)
        )

        return self.db.scalar(stmt)

    # ---------------------------------------------------------
    # Item
    # ---------------------------------------------------------

    def get_item(
        self,
        code: str,
    ) -> MarketItem | None:

        stmt = (
            select(MarketItem)
            .where(MarketItem.code == code)
        )

        return self.db.scalar(stmt)

    # ---------------------------------------------------------
    # Latest
    # ---------------------------------------------------------

    def get_latest(

        self,

        item_id: int,

        provider_id: int,

    ) -> MarketPriceLatest | None:

        stmt = (

            select(MarketPriceLatest)

            .where(

                MarketPriceLatest.item_id == item_id,

                MarketPriceLatest.provider_id == provider_id,

            )

        )

        return self.db.scalar(stmt)

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    def is_cache_valid(

        self,

        latest: MarketPriceLatest | None,

        minutes: int = 5,

    ) -> bool:

        if latest is None:

            return False

        return latest.retrieved_at >= (

            datetime.utcnow()

            - timedelta(minutes=minutes)

        )

    # ---------------------------------------------------------
    # Insert History
    # ---------------------------------------------------------

    def append_history(

        self,

        entity: MarketPriceHistory,

    ):

        self.db.add(entity)

    # ---------------------------------------------------------
    # Save Latest
    # ---------------------------------------------------------

    def save_latest(

        self,

        entity: MarketPriceLatest,

    ):

        self.db.merge(entity)

    # ---------------------------------------------------------
    # Commit
    # ---------------------------------------------------------

    def commit(self):

        self.db.commit()