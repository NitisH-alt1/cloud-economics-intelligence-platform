import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
DATABASE_URL = os.getenv("DATABASE_URL")
if APP_ENV == "production" and not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set when APP_ENV=production.")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg2://cea_admin:cea_local_password@localhost:5433/cloud_economics"


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
