"""
Database connection factories for PostgreSQL and Qdrant.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from qdrant_client import QdrantClient
from contextlib import contextmanager
from typing import Generator
import logging

from .settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# SQLAlchemy Engine
engine = create_engine(
    settings.postgres_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_qdrant_client() -> QdrantClient:
    """
    Get Qdrant client instance.

    Returns:
        QdrantClient: Configured Qdrant client
    """
    client = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        timeout=30
    )
    return client


def init_database():
    """Initialize database schema."""
    from src.models.postgres_models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    logger.info("Database schema initialized")
