from app.database.database import SessionLocal

from app.repository.market_repository import MarketRepository


db = SessionLocal()

repo = MarketRepository(db)

print()

print(repo.get_provider("navasan"))

print()

print(repo.get_item("usd"))