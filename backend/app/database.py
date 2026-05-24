from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.config import settings

# Create engine with NullPool for serverless compatibility
# pool_pre_ping=True helps detect dropped connections
engine = create_engine(
    settings.get_database_url,
    pool_pre_ping=True,
    poolclass=NullPool,
)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function for FastAPI routes to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    No-op in production — Alembic manages all DDL via migrations.
    Run `alembic upgrade head` before starting the server.

    Left here so the startup event in main.py doesn't need to change,
    and so local developers can still call it for quick in-process table
    creation during tests by passing create_tables=True.
    """
    pass


def create_tables_for_testing() -> None:
    """Only for use in tests that need an in-memory DB without running Alembic."""
    from app.models import Base
    Base.metadata.create_all(bind=engine)

