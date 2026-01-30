#!/usr/bin/env python
"""
Initialize Qdrant collection.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client.models import Distance, VectorParams
from src.config.database import get_qdrant_client
from src.config.settings import settings
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def init_qdrant():
    """Create Qdrant collection."""
    try:
        client = get_qdrant_client()

        collection_name = settings.qdrant_collection
        logger.info(f"Creating Qdrant collection: {collection_name}")

        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name in collection_names:
            logger.warning(f"Collection '{collection_name}' already exists")
            response = input("Delete and recreate? (y/N): ")
            if response.lower() == 'y':
                client.delete_collection(collection_name)
                logger.info(f"Deleted existing collection '{collection_name}'")
            else:
                logger.info("Skipping collection creation")
                return

        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,
                distance=Distance.COSINE
            )
        )

        logger.info(f"Collection '{collection_name}' created successfully")

        # Verify collection
        info = client.get_collection(collection_name)
        logger.info(f"Collection info: {info}")

    except Exception as e:
        logger.error(f"Failed to create Qdrant collection: {e}")
        raise


if __name__ == "__main__":
    init_qdrant()
