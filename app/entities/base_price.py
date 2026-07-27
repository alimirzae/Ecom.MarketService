from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class BasePriceMixin:
    """
    Shared columns between Latest and History tables.
    """

    item_id: Mapped[int] = mapped_column(
        ForeignKey("market_item.id"),
        nullable=False,
        index=True,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("market_provider.id"),
        nullable=False,
        index=True,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    change_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    provider_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    provider_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )