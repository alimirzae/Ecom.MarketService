import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.database.database import engine

with engine.connect() as conn:

    version = conn.execute(
        text("SELECT VERSION()")
    ).scalar()

    print(version)