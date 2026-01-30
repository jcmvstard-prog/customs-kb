"""
Semantic search using vector similarity.
"""
from typing import List, Dict, Any, Optional
import numpy as np

from src.config.database import get_db_session, get_qdrant_client
from src.storage.postgres_store import PostgresStore
from src.storage.qdrant_store import QdrantStore
from src.ingest.embeddings import get_embedding_generator
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SemanticSearch:
    """Semantic search engine."""

    def __init__(self):
        """Initialize semantic search."""
        self.embedding_generator = get_embedding_generator()
        self.qdrant_client = get_qdrant_client()
        self.qdrant_store = QdrantStore(self.qdrant_client)

    def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        hts_codes: Optional[List[str]] = None,
        agencies: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query: Search query text
            limit: Maximum results
            score_threshold: Minimum similarity score
            hts_codes: Filter by HTS codes
            agencies: Filter by agencies
            source: Filter by source

        Returns:
            List[Dict[str, Any]]: Search results with metadata
        """
        logger.info(f"Semantic search query: {query}")

        # Generate query embedding
        query_embedding = self.embedding_generator.embed_text(query)

        # Search Qdrant
        qdrant_results = self.qdrant_store.search(
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            hts_codes=hts_codes,
            agencies=agencies,
            source=source
        )

        if not qdrant_results:
            logger.info("No results found")
            return []

        # Hydrate results with PostgreSQL data
        results = []
        seen_documents = set()

        with get_db_session() as db_session:
            postgres_store = PostgresStore(db_session)

            for qdrant_result in qdrant_results:
                payload = qdrant_result['payload']
                document_id = payload['document_id']

                # Skip duplicate documents (multiple chunks)
                if document_id in seen_documents:
                    continue

                seen_documents.add(document_id)

                # Get full document from PostgreSQL
                document = postgres_store.get_document_by_id(document_id)

                if document:
                    result = {
                        'document_number': document.document_number,
                        'title': document.title,
                        'abstract': document.abstract,
                        'publication_date': document.publication_date.isoformat() if document.publication_date else None,
                        'source': document.source,
                        'document_type': document.document_type,
                        'html_url': document.html_url,
                        'score': qdrant_result['score'],
                        'matched_chunk': payload['text_chunk'][:200] + '...',
                        'agencies': [a.name for a in document.agencies],
                        'hts_codes': [h.hts_number for h in document.hts_codes]
                    }

                    results.append(result)

        logger.info(f"Found {len(results)} results")
        return results

    def search_by_document_number(self, document_number: str) -> Optional[Dict[str, Any]]:
        """
        Get document by document number.

        Args:
            document_number: Document number

        Returns:
            Optional[Dict[str, Any]]: Document details or None
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
