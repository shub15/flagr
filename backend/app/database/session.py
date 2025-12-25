"""
Database session management and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.database import Base
from app.config import settings
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Create database engine with dual-mode support
# Automatically detects SQLite vs PostgreSQL from DATABASE_URL
is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    # SQLite configuration (for local development)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
        echo=settings.debug,
        pool_pre_ping=True
    )
    logger.info("Using SQLite database (local mode)")
else:
    # PostgreSQL configuration (for Supabase/production)
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,        # Connection pool size
        max_overflow=20      # Max connections beyond pool_size
    )
    logger.info("Using PostgreSQL database (production mode)")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running this module directly to initialize the database
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete")
