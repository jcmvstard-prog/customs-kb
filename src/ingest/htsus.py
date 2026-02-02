"""
HTSUS (Harmonized Tariff Schedule) data ingestion.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
import pandas as pd
from tqdm import tqdm

from src.ingest.base_ingester import BaseIngester
from src.config.database import get_db_session
from src.config.settings import settings
from src.storage.postgres_store import PostgresStore
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HTSUSIngester(BaseIngester):
    """Ingest HTSUS tariff data."""

    def __init__(self):
        """Initialize ingester."""
        super().__init__()
        self.data_dir = Path("data/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Fetch HTSUS data from USITC.

        Args:
            url: URL to download from (optional, defaults to USITC 2025 basic edition)

        Returns:
            pd.DataFrame: HTSUS data
        """
        if url is None:
            url = "https://www.usitc.gov/sites/default/files/tata/hts/hts_2025_basic_edition_csv.csv"

        local_file = self.data_dir / "htsus_2025_basic.csv"

        # Download if not cached
        if not local_file.exists():
            logger.info(f"Downloading HTSUS data from {url}")
            response = httpx.get(url, follow_redirects=True, timeout=120.0)
            response.raise_for_status()
            local_file.write_bytes(response.content)
            logger.info(f"Downloaded {len(response.content)} bytes to {local_file}")
        else:
            logger.info(f"Using cached HTSUS data from {local_file}")

        # Read CSV with proper encoding
        df = pd.read_csv(
            local_file,
            encoding='utf-8-sig',  # Handle BOM
            dtype=str  # Read all as strings initially
        )

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Filter to only rows with HTS numbers (skip header rows without codes)
        df = df[df['hts_number'].notna() & (df['hts_number'].str.strip() != '')]

        logger.info(f"Loaded {len(df)} HTSUS entries")
        return df

    def transform(self, raw_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Transform HTSUS data.

        Args:
            raw_data: Raw DataFrame

        Returns:
            Dict[str, Any]: Transformed HTS codes
        """
        hts_codes = []

        logger.info("Transforming HTSUS data...")

        # Track parent codes for hierarchy
        parents_by_level = {}

        for _, row in tqdm(raw_data.iterrows(), total=len(raw_data), desc="Processing HTS codes"):
            hts_number = str(row['hts_number']).strip()
            indent_str = str(row.get('indent', '')).strip()

            # Convert indent to int, default to 0
            try:
                indent_level = int(indent_str) if indent_str else 0
            except ValueError:
                indent_level = 0

            description = str(row.get('description', '')).strip()
            general_rate = str(row.get('general_rate_of_duty', '')).strip()
            special_rate = str(row.get('special_rate_of_duty', '')).strip()

            # Determine parent based on indent hierarchy
            parent_hts_number = None
            if indent_level > 0:
                # Find parent from previous level
                for level in range(indent_level - 1, -1, -1):
                    if level in parents_by_level:
                        parent_hts_number = parents_by_level[level]
                        break

            # Store this code as potential parent for future codes
            parents_by_level[indent_level] = hts_number
            # Clear deeper levels
            parents_by_level = {k: v for k, v in parents_by_level.items() if k <= indent_level}

            hts_code = {
                'hts_number': hts_number,
                'indent_level': indent_level,
                'description': description,
                'general_rate': general_rate if general_rate and general_rate != 'nan' else None,
                'special_rate': special_rate if special_rate and special_rate != 'nan' else None,
                'parent_hts_number': parent_hts_number,
                'effective_date': None
            }

            hts_codes.append(hts_code)

        logger.info(f"Transformed {len(hts_codes)} HTS codes")

        return {
            'hts_codes': hts_codes,
            'count': len(hts_codes)
        }

    def load(self, data: Dict[str, Any]) -> bool:
        """
        Load HTS codes into PostgreSQL.

        Args:
            data: Transformed HTS codes

        Returns:
            bool: Success status
        """
        hts_codes = data.get('hts_codes', [])

        if not hts_codes:
            logger.warning("No HTS codes to load")
            return False

        try:
            with get_db_session() as db_session:
                postgres_store = PostgresStore(db_session)

                # Create ingestion run
                ingestion_run = postgres_store.create_ingestion_run('htsus')

                logger.info(f"Loading {len(hts_codes)} HTS codes to database...")

                # Bulk upsert HTS codes
                for hts_code_data in tqdm(hts_codes, desc="Upserting HTS codes"):
                    postgres_store.get_or_create_hts_code(hts_code_data)

                # Commit and update ingestion run
                db_session.commit()
                postgres_store.complete_ingestion_run(
                    ingestion_run.id,
                    documents_processed=len(hts_codes)
                )

                logger.info(f"Successfully loaded {len(hts_codes)} HTS codes")
                return True

        except Exception as e:
            logger.error(f"Error loading HTS codes: {e}", exc_info=True)
            return False

    def ingest(self, **kwargs) -> bool:
        """
        Run full HTSUS ingestion pipeline.

        Returns:
            bool: Success status
        """
        try:
            # Fetch
            raw_data = self.fetch(**kwargs)

            # Transform
            transformed_data = self.transform(raw_data)

            # Load
            success = self.load(transformed_data)

            return success

        except Exception as e:
            logger.error(f"HTSUS ingestion failed: {e}", exc_info=True)
            return False
