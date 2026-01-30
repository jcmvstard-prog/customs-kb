"""
Structured queries using PostgreSQL.
"""
from typing import List, Dict, Any, Optional
from datetime import date

from src.config.database import get_db_session
from src.storage.postgres_store import PostgresStore
from src.models.postgres_models import HTSCode
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class StructuredQuery:
    """Structured query interface."""

    def __init__(self):
        """Initialize structured query."""
        pass

    def get_document_by_number(self, document_number: str) -> Optional[Dict[str, Any]]:
        """
        Get document by document number.

        Args:
            document_number: Document number

        Returns:
            Optional[Dict[str, Any]]: Document or None
        """
        with get_db_session() as db_session:
            postgres_store = PostgresStore(db_session)
            document = postgres_store.get_document_by_number(document_number)

            if not document:
                return None

            return {
                'document_number': document.document_number,
                'title': document.title,
                'abstract': document.abstract,
                'full_text': document.full_text,
                'publication_date': document.publication_date.isoformat() if document.publication_date else None,
                'source': document.source,
                'document_type': document.document_type,
                'html_url': document.html_url,
                'agencies': [{'slug': a.slug, 'name': a.name} for a in document.agencies],
                'hts_codes': [
                    {
                        'hts_number': h.hts_number,
                        'description': h.description,
                        'general_rate': h.general_rate
                    }
                    for h in document.hts_codes
                ]
            }

    def search_by_date_range(
        self,
        start_date: date,
        end_date: date,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search documents by date range.

        Args:
            start_date: Start date
            end_date: End date
            source: Filter by source
            limit: Maximum results

        Returns:
            List[Dict[str, Any]]: List of documents
        """
        with get_db_session() as db_session:
            postgres_store = PostgresStore(db_session)
            documents = postgres_store.search_documents(
                source=source,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            results = []
            for document in documents:
                results.append({
                    'document_number': document.document_number,
                    'title': document.title,
                    'abstract': document.abstract,
                    'publication_date': document.publication_date.isoformat() if document.publication_date else None,
                    'source': document.source,
                    'document_type': document.document_type,
                    'html_url': document.html_url,
                    'agencies': [a.name for a in document.agencies],
                    'hts_codes': [h.hts_number for h in document.hts_codes]
                })

            return results

    def get_hts_code_info(self, hts_number: str) -> Optional[Dict[str, Any]]:
        """
        Get HTS code information.

        Args:
            hts_number: HTS code number

        Returns:
            Optional[Dict[str, Any]]: HTS code info or None
        """
        with get_db_session() as db_session:
            hts_code = db_session.query(HTSCode).filter_by(
                hts_number=hts_number
            ).first()

            if not hts_code:
                return None

            return {
                'hts_number': hts_code.hts_number,
                'description': hts_code.description,
                'indent_level': hts_code.indent_level,
                'general_rate': hts_code.general_rate,
                'special_rate': hts_code.special_rate,
                'parent_hts_number': hts_code.parent_hts_number,
                'effective_date': hts_code.effective_date.isoformat() if hts_code.effective_date else None,
                'related_documents': len(hts_code.documents)
            }

    def search_hts_codes(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search HTS codes by description.

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            List[Dict[str, Any]]: List of HTS codes
        """
        with get_db_session() as db_session:
            hts_codes = db_session.query(HTSCode).filter(
                HTSCode.description.ilike(f'%{search_term}%')
            ).limit(limit).all()

            results = []
            for hts_code in hts_codes:
                results.append({
                    'hts_number': hts_code.hts_number,
                    'description': hts_code.description,
                    'general_rate': hts_code.general_rate,
                    'special_rate': hts_code.special_rate
                })

            return results

    def get_documents_by_hts_code(self, hts_number: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get documents related to an HTS code.

        Args:
            hts_number: HTS code number
            limit: Maximum results

        Returns:
            List[Dict[str, Any]]: List of documents
        """
        with get_db_session() as db_session:
            hts_code = db_session.query(HTSCode).filter_by(
                hts_number=hts_number
            ).first()

            if not hts_code:
                return []

            documents = hts_code.documents[:limit]

            results = []
            for document in documents:
                results.append({
                    'document_number': document.document_number,
                    'title': document.title,
                    'abstract': document.abstract,
                    'publication_date': document.publication_date.isoformat() if document.publication_date else None,
                    'source': document.source,
                    'html_url': document.html_url
                })

            return results
