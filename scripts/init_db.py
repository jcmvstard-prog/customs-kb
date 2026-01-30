#!/usr/bin/env python
"""
Initialize PostgreSQL database schema.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.database import engine, Base
from src.models.postgres_models import (
    Document, Agency, HTSCode, IngestionRun,
    document_agencies, document_hts_codes
)
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def init_db():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


if __name__ == "__main__":
    init_db()
