from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Import models so SQLAlchemy registers tables
    from app.domain import models  # noqa: F401

    Base.metadata.create_all(bind=engine)