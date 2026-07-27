from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class MarketProvider(Base):

    __tablename__ = "market_provider"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


    from sqlalchemy.orm import relationship

    latest_prices = relationship(
        "MarketPriceLatest",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    history_prices = relationship(
        "MarketPriceHistory",
        back_populates="provider",
        cascade="all, delete-orphan",
    )