from app.database.base import Base
from app.database.database import engine

# Register all entities
from app.entities import (
    MarketProvider,
    MarketItem,
    MarketPriceLatest,
    MarketPriceHistory,
)


def create_database():

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":

    create_database()

    print("Database schema created successfully.")