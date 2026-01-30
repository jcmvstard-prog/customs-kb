"""
Federal Register API client and ingestion pipeline.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import httpx
from tqdm import tqdm

from src.ingest.base_ingester import BaseIngester
from src.config.settings import settings
from src.config.database import get_db_session, get_qdrant_client
from src.storage.postgres_store import PostgresStore
from src.storage.qdrant_store import QdrantStore
from src.ingest.embeddings import get_embedding_generator
from src.utils.text_processing import strip_html, extract_hts_codes
from src.utils.retry import retry_on_http_error
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class FederalRegisterClient:
    """Client for Federal Register API."""

    def __init__(self):
        """Initialize Federal Register client."""
        self.base_url = settings.federal_register_base_url
        self.agency = settings.federal_register_agency
        self.client = httpx.Client(timeout=30.0)

    @retry_on_http_error()
    def fetch_documents(
        self,
        start_date: date,
        end_date: date,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch documents from Federal Register API.

        Args:
            start_date: Start date
            end_date: End date
            page: Page number
            per_page: Results per page

        Returns:
            Dict[str, Any]: API response
        """
        url = f"{self.base_url}/documents"
        params = {
            'conditions[agencies][]': self.agency,
            'conditions[publication_date][gte]': start_date.isoformat(),
            'conditions[publication_date][lte]': end_date.isoformat(),
            'per_page': per_page,
            'page': page,
            'order': 'oldest'
        }

        logger.debug(f"Fetching page {page} from Federal Register API")
        response = self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def fetch_all_documents(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch all documents for date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[Dict[str, Any]]: List of documents
        """
        all_documents = []
        page = 1
        total_pages = None

        logger.info(f"Fetching Federal Register documents from {start_date} to {end_date}")

        while True:
            response = self.fetch_documents(start_date, end_date, page=page)

            documents = response.get('results', [])
            all_documents.extend(documents)

            if total_pages is None:
                total_pages = response.get('total_pages', 1)
                logger.info(f"Total pages: {total_pages}")

            logger.info(f"Fetched page {page}/{total_pages} ({len(documents)} documents)")

            if page >= total_pages:
                break

            page += 1

        logger.info(f"Fetched {len(all_documents)} total documents")
        return all_documents

    def close(self):
        """Close HTTP client."""
        self.client.close()


class FederalRegisterIngester(BaseIngester):
    """Ingest Federal Register documents into database."""

    def __init__(self):
        """Initialize ingester."""
        super().__init__()
        self.client = FederalRegisterClient()
        self.embedding_generator = get_embedding_generator()

    def fetch(
        self,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch documents from Federal Register.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[Dict[str, Any]]: List of documents
        """
        return self.client.fetch_all_documents(start_date, end_date)

    def transform(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform Federal Register documents.

        Args:
            raw_data: Raw API documents

        Returns:
            Dict[str, Any]: Transformed documents
        """
        transformed = []

        for doc in raw_data:
            # Extract full text (combine abstract and body)
            abstract = doc.get('abstract', '') or ''
            body = doc.get('body_html_url', '')

            # For POC, we'll use abstract and full text URL
            # In production, fetch full HTML from body_html_url
            full_text = strip_html(abstract)

            # Parse publication date
            pub_date_str = doc.get('publication_date')
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
                except:
                    pass

            # Extract HTS codes from text
            hts_codes = extract_hts_codes(full_text)

            # Extract agencies
            agencies = [
                agency.get('slug')
                for agency in doc.get('agencies', [])
                if agency.get('slug')
            ]

            transformed_doc = {
                'document_number': doc.get('document_number'),
                'source': 'federal_register',
                'document_type': doc.get('type'),
                'title': doc.get('title'),
                'abstract': abstract,
                'publication_date': pub_date,
                'html_url': doc.get('html_url'),
                'full_text': full_text,
                'agencies': agencies,
                'agency_names': [a.get('name') for a in doc.get('agencies', [])],
                'hts_codes': hts_codes
            }

            transformed.append(transformed_doc)

        return {
            'documents': transformed,
            'count': len(transformed)
        }

    def load(self, data: Dict[str, Any]) -> bool:
        """
        Load documents into PostgreSQL and Qdrant.

        Args:
            data: Transformed documents

        Returns:
            bool: Success status
        """
        documents = data.get('documents', [])

        if not documents:
            logger.warning("No documents to load")
            return False

        try:
            with get_db_session() as db_session:
                postgres_store = PostgresStore(db_session)
                qdrant_client = get_qdrant_client()
                qdrant_store = QdrantStore(qdrant_client)

                # Create ingestion run
                ingestion_run = postgres_store.create_ingestion_run('federal_register')

                processed = 0
                errors = []

                for doc_data in tqdm(documents, desc="Loading documents"):
                    try:
                        # Create document
                        document = postgres_store.create_document({
                            'document_number': doc_data['document_number'],
                            'source': doc_data['source'],
                            'document_type': doc_data['document_type'],
                            'title': doc_data['title'],
                            'abstract': doc_data['abstract'],
                            'publication_date': doc_data['publication_date'],
                            'html_url': doc_data['html_url'],
                            'full_text': doc_data['full_text']
                        })

                        # Create agencies
                        for agency_slug, agency_name in zip(
                            doc_data['agencies'],
                            doc_data['agency_names']
                        ):
                            postgres_store.get_or_create_agency(agency_slug, agency_name)

                        # Link agencies
                        postgres_store.link_document_agencies(
                            document,
                            doc_data['agencies']
                        )

                        # Link HTS codes (if they exist in database)
                        if doc_data['hts_codes']:
                            postgres_store.link_document_hts_codes(
                                document,
                                doc_data['hts_codes']
                            )

                        db_session.flush()

                        # Generate embeddings
                        chunks_with_embeddings = self.embedding_generator.chunk_and_embed(
                            doc_data['full_text']
                        )

                        # Create Qdrant points
                        if chunks_with_embeddings:
                            points = qdrant_store.create_document_points(
                                document_id=document.id,
                                document_number=document.document_number,
                                source=document.source,
                                title=document.title,
                                publication_date=document.publication_date.isoformat() if document.publication_date else None,
                                chunks_with_embeddings=chunks_with_embeddings,
                                hts_codes=doc_data['hts_codes'],
                                agencies=doc_data['agencies']
                            )

                            qdrant_store.upsert_points(points)

                        processed += 1

                    except Exception as e:
                        logger.error(f"Failed to process document {doc_data.get('document_number')}: {e}")
                        errors.append(str(e))

                # Update ingestion run
                status = 'completed' if processed > 0 else 'failed'
                postgres_store.update_ingestion_run(
                    ingestion_run.id,
                    status=status,
                    documents_processed=processed
                )

                logger.info(f"Loaded {processed} documents successfully")

                if errors:
                    logger.warning(f"Encountered {len(errors)} errors during ingestion")

                return processed > 0

        except Exception as e:
            logger.error(f"Load failed: {e}")
            return False
        finally:
            self.client.close()
