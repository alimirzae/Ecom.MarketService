from app.database.database import SessionLocal

from app.entities.market_provider import MarketProvider
from app.entities.market_item import MarketItem


db = SessionLocal()


def seed_providers():

    if db.query(MarketProvider).count() > 0:
        return

    db.add_all([
        MarketProvider(
            name="navasan",
            display_name="Navasan Widget",
            base_url="https://www.navasan.tech",
            active=True,
        ),
    ])


def seed_items():

    if db.query(MarketItem).count() > 0:
        return

    db.add_all([

        MarketItem(
            code="usd",
            title="دلار آمریکا",
            category="currency",
            unit="IRT",
            active=True,
        ),

        MarketItem(
            code="eur",
            title="یورو",
            category="currency",
            unit="IRT",
            active=True,
        ),

        MarketItem(
            code="18ayar",
            title="طلای ۱۸ عیار",
            category="gold",
            unit="IRT",
            active=True,
        ),

        MarketItem(
            code="sekkeh",
            title="سکه امامی",
            category="coin",
            unit="IRT",
            active=True,
        ),
    ])


def main():

    seed_providers()

    seed_items()

    db.commit()

    print("Seed completed.")


if __name__ == "__main__":

    main()