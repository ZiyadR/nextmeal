from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

# Database URL - SQLite file in backend directory
# Can be overridden with DATABASE_URL environment variable for Docker
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nextmeal.db")

# Create engine with connection pooling for SQLite
# check_same_thread=False is needed for FastAPI to work with SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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


def init_db():
    """
    Initialize the database by creating all tables.
    This is called when the app starts if using direct table creation.
    For production, use Alembic migrations instead.
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)
