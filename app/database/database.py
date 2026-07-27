from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


DATABASE_URL = (
    f"mysql+pymysql://"
    f"{settings.MYSQL_USER}:"
    f"{settings.MYSQL_PASSWORD}@"
    f"{settings.MYSQL_HOST}:"
    f"{settings.MYSQL_PORT}/"
    f"{settings.MYSQL_DATABASE}"
    "?charset=utf8mb4"
)

engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    echo=True,

)

SessionLocal = sessionmaker(

    bind=engine,

    autoflush=False,

    autocommit=False,

)