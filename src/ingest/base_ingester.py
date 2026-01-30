"""
Base ingester class for data ingestion pipelines.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseIngester(ABC):
    """Abstract base class for data ingesters."""

    def __init__(self):
        """Initialize ingester."""
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """
        Fetch raw data from source.

        Returns:
            Any: Raw data
        """
        pass

    @abstractmethod
    def transform(self, raw_data: Any) -> Dict[str, Any]:
        """
        Transform raw data into structured format.

        Args:
            raw_data: Raw data from fetch

        Returns:
            Dict[str, Any]: Transformed data
        """
        pass

    @abstractmethod
    def load(self, data: Dict[str, Any]) -> bool:
        """
        Load data into database.

        Args:
            data: Transformed data

        Returns:
            bool: Success status
        """
        pass

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute full ETL pipeline.

        Args:
            **kwargs: Arguments passed to fetch

        Returns:
            Dict[str, Any]: Ingestion statistics
        """
        start_time = datetime.now()
        stats = {
            'started_at': start_time.isoformat(),
            'status': 'running',
            'records_processed': 0,
            'errors': []
        }

        try:
            # Fetch
            self.logger.info("Fetching data...")
            raw_data = self.fetch(**kwargs)

            # Transform
            self.logger.info("Transforming data...")
            transformed_data = self.transform(raw_data)

            # Load
            self.logger.info("Loading data...")
            success = self.load(transformed_data)

            stats['status'] = 'completed' if success else 'failed'
            stats['records_processed'] = transformed_data.get('count', 0)

        except Exception as e:
            self.logger.error(f"Ingestion failed: {e}")
            stats['status'] = 'failed'
            stats['errors'].append(str(e))

        finally:
            end_time = datetime.now()
            stats['completed_at'] = end_time.isoformat()
            stats['duration_seconds'] = (end_time - start_time).total_seconds()

        return stats
