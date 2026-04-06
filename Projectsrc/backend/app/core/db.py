from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Import models so SQLAlchemy registers tables
    from app.domain import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Add filename column to existing data_assets table if not present
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS filename VARCHAR(256)"
        ))
        conn.commit()