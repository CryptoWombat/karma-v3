"""Database session management."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.environment == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for DB session (use outside FastAPI)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call on startup."""
    from app.models import user, wallet, transaction, referral, validator_key, protocol  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all tables. Use only in tests."""
    Base.metadata.drop_all(bind=engine)
