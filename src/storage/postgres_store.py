"""
PostgreSQL storage operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.postgres_models import Document, Agency, HTSCode, IngestionRun
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PostgresStore:
    """PostgreSQL database operations."""

    def __init__(self, session: Session):
        """
        Initialize store with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create_document(self, document_data: Dict[str, Any]) -> Document:
        """
        Create or update a document.

        Args:
            document_data: Document fields

        Returns:
            Document: Created or updated document
        """
        # Check if document exists
        existing = self.session.query(Document).filter_by(
            document_number=document_data['document_number']
        ).first()

        if existing:
            # Update existing document
            for key, value in document_data.items():
                if key not in ['agencies', 'hts_codes']:
                    setattr(existing, key, value)
            logger.debug(f"Updated document: {existing.document_number}")
            return existing
        else:
            # Create new document
            document = Document(**{
                k: v for k, v in document_data.items()
                if k not in ['agencies', 'hts_codes']
            })
            self.session.add(document)
            self.session.flush()
            logger.debug(f"Created document: {document.document_number}")
            return document

    def get_or_create_agency(self, slug: str, name: str) -> Agency:
        """
        Get existing agency or create new one.

        Args:
            slug: Agency slug
            name: Agency name

        Returns:
            Agency: Agency object
        """
        agency = self.session.query(Agency).filter_by(slug=slug).first()

        if not agency:
            agency = Agency(slug=slug, name=name)
            self.session.add(agency)
            self.session.flush()
            logger.debug(f"Created agency: {slug}")

        return agency

    def get_or_create_hts_code(self, hts_data: Dict[str, Any]) -> HTSCode:
        """
        Get existing HTS code or create new one.

        Args:
            hts_data: HTS code fields

        Returns:
            HTSCode: HTS code object
        """
        hts_code = self.session.query(HTSCode).filter_by(
            hts_number=hts_data['hts_number']
        ).first()

        if not hts_code:
            hts_code = HTSCode(**hts_data)
            self.session.add(hts_code)
            self.session.flush()
            logger.debug(f"Created HTS code: {hts_data['hts_number']}")

        return hts_code

    def link_document_agencies(self, document: Document, agency_slugs: List[str]):
        """
        Link document to agencies.

        Args:
            document: Document object
            agency_slugs: List of agency slugs
        """
        agencies = self.session.query(Agency).filter(
            Agency.slug.in_(agency_slugs)
        ).all()

        document.agencies = agencies

    def link_document_hts_codes(self, document: Document, hts_numbers: List[str]):
        """
        Link document to HTS codes.

        Args:
            document: Document object
            hts_numbers: List of HTS numbers
        """
        hts_codes = self.session.query(HTSCode).filter(
            HTSCode.hts_number.in_(hts_numbers)
        ).all()

        document.hts_codes = hts_codes

    def get_document_by_number(self, document_number: str) -> Optional[Document]:
        """
        Get document by document number.

        Args:
            document_number: Document number

        Returns:
            Optional[Document]: Document or None
        """
        return self.session.query(Document).filter_by(
            document_number=document_number
        ).first()

    def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """
        Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Optional[Document]: Document or None
        """
        return self.session.query(Document).filter_by(id=document_id).first()

    def search_documents(
        self,
        source: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Document]:
        """
        Search documents with filters.

        Args:
            source: Filter by source
            start_date: Filter by publication date start
            end_date: Filter by publication date end
            limit: Maximum results

        Returns:
            List[Document]: List of documents
        """
        query = self.session.query(Document)

        if source:
            query = query.filter(Document.source == source)

        if start_date:
            query = query.filter(Document.publication_date >= start_date)

        if end_date:
            query = query.filter(Document.publication_date <= end_date)

        return query.order_by(Document.publication_date.desc()).limit(limit).all()

    def create_ingestion_run(self, source: str) -> IngestionRun:
        """
        Create new ingestion run.

        Args:
            source: Data source name

        Returns:
            IngestionRun: Created ingestion run
        """
        run = IngestionRun(source=source, status='running')
        self.session.add(run)
        self.session.flush()
        logger.info(f"Created ingestion run {run.id} for source: {source}")
        return run

    def update_ingestion_run(
        self,
        run_id: int,
        status: str,
        documents_processed: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Update ingestion run.

        Args:
            run_id: Ingestion run ID
            status: New status
            documents_processed: Number of documents processed
            error_message: Error message if failed
        """
        run = self.session.query(IngestionRun).filter_by(id=run_id).first()

        if run:
            run.status = status
            if documents_processed is not None:
                run.documents_processed = documents_processed
            if error_message:
                run.error_message = error_message
            if status in ['completed', 'failed']:
                run.completed_at = datetime.utcnow()

            logger.info(f"Updated ingestion run {run_id}: {status}")

    def complete_ingestion_run(self, run_id: int, documents_processed: int):
        """
        Mark ingestion run as completed.

        Args:
            run_id: Ingestion run ID
            documents_processed: Number of documents processed
        """
        self.update_ingestion_run(run_id, 'completed', documents_processed)

    def get_last_ingestion_run(self, source: str) -> Optional[IngestionRun]:
        """
        Get last completed ingestion run for a source.

        Args:
            source: Data source name

        Returns:
            Optional[IngestionRun]: Last ingestion run or None
        """
        return self.session.query(IngestionRun).filter_by(
            source=source, status='completed'
        ).order_by(IngestionRun.completed_at.desc()).first()

    def get_document_count(self) -> int:
        """Get total number of documents."""
        return self.session.query(Document).count()

    def get_hts_count(self) -> int:
        """Get total number of HTS codes."""
        return self.session.query(HTSCode).count()

    def get_recent_ingestion_runs(self, limit: int = 10) -> List[IngestionRun]:
        """Get recent ingestion runs."""
        return self.session.query(IngestionRun).order_by(
            IngestionRun.started_at.desc()
        ).limit(limit).all()
