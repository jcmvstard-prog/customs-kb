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

# Sample HTSUS data source (for POC, using a simplified approach)
HTSUS_SAMPLE_URL = "https://hts.usitc.gov/export/2024-HTSARev1.csv"


class HTSUSIngester(BaseIngester):
    """Ingest HTSUS tariff data."""

    def __init__(self):
        """Initialize ingester."""
        super().__init__()
        self.data_dir = Path("data/raw")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Fetch HTSUS data.

        For POC, we'll create sample data. In production, download from Data.gov.

        Args:
            url: URL to download from (optional)

        Returns:
            pd.DataFrame: HTSUS data
        """
        # For POC, create sample HTSUS data
        # In production, download actual CSV from USITC or Data.gov
        logger.info("Creating sample HTSUS data for POC")

        sample_data = [
            {
                'hts_number': '0406.10.00',
                'indent_level': 2,
                'description': 'Fresh (unripened or uncured) cheese',
                'general_rate': '10%',
                'special_rate': 'Free (A+,AU,BH,CA,CL,CO,D,E,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '0406.00.00'
            },
            {
                'hts_number': '0406.20.00',
                'indent_level': 2,
                'description': 'Grated or powdered cheese',
                'general_rate': '8%',
                'special_rate': 'Free (A,AU,BH,CA,CL,CO,D,E,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '0406.00.00'
            },
            {
                'hts_number': '0406.30.00',
                'indent_level': 2,
                'description': 'Processed cheese',
                'general_rate': '10%',
                'special_rate': 'Free (A+,AU,BH,CA,CL,CO,D,E,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '0406.00.00'
            },
            {
                'hts_number': '0406.40.00',
                'indent_level': 2,
                'description': 'Blue-veined cheese',
                'general_rate': '10%',
                'special_rate': 'Free (A+,AU,BH,CA,CL,CO,D,E,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '0406.00.00'
            },
            {
                'hts_number': '0406.90.00',
                'indent_level': 2,
                'description': 'Other cheese',
                'general_rate': '10%',
                'special_rate': 'Free (A+,AU,BH,CA,CL,CO,D,E,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '0406.00.00'
            },
            {
                'hts_number': '6204.11.00',
                'indent_level': 2,
                'description': 'Women\'s suits, of wool or fine animal hair',
                'general_rate': '16%',
                'special_rate': 'Free (AU,BH,CA,CL,CO,IL,JO,KR,MA,MX,OM,P,PA,PE,S,SG)',
                'parent_hts_number': '6204.00.00'
            },
            {
                'hts_number': '7208.10.00',
                'indent_level': 2,
                'description': 'Flat-rolled products of iron or steel',
                'general_rate': 'Free',
                'special_rate': 'Free',
                'parent_hts_number': '7208.00.00'
            },
            {
                'hts_number': '8471.30.00',
                'indent_level': 2,
                'description': 'Portable automatic data processing machines',
                'general_rate': 'Free',
                'special_rate': 'Free',
                'parent_hts_number': '8471.00.00'
            },
            {
                'hts_number': '9401.20.00',
                'indent_level': 2,
                'description': 'Seats of a kind used for motor vehicles',
                'general_rate': 'Free',
                'special_rate': 'Free',
                'parent_hts_number': '9401.00.00'
            },
        ]

        df = pd.DataFrame(sample_data)
        logger.info(f"Created sample HTSUS data with {len(df)} codes")

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

        for _, row in raw_data.iterrows():
            hts_code = {
                'hts_number': row['hts_number'],
                'indent_level': row['indent_level'],
                'description': row['description'],
                'general_rate': row['general_rate'],
                'special_rate': row['special_rate'],
                'parent_hts_number': row.get('parent_hts_number'),
                'effective_date': None  # POC: no date filtering
            }

            hts_codes.append(hts_code)

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

                processed = 0

                for hts_data in tqdm(hts_codes, desc="Loading HTS codes"):
                    try:
                        postgres_store.get_or_create_hts_code(hts_data)
                        processed += 1
                    except Exception as e:
                        logger.error(f"Failed to load HTS code {hts_data['hts_number']}: {e}")

                # Update ingestion run
                status = 'completed' if processed > 0 else 'failed'
                postgres_store.update_ingestion_run(
                    ingestion_run.id,
                    status=status,
                    documents_processed=processed
                )

                logger.info(f"Loaded {processed} HTS codes successfully")
                return processed > 0

        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False
