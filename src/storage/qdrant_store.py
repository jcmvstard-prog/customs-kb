"""
Qdrant vector storage operations.
"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
from uuid import uuid4

from src.config.settings import settings
from src.models.qdrant_schemas import DocumentPayload
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class QdrantStore:
    """Qdrant vector database operations."""

    def __init__(self, client: QdrantClient):
        """
        Initialize store with Qdrant client.

        Args:
            client: Qdrant client
        """
        self.client = client
        self.collection_name = settings.qdrant_collection

    def upsert_points(self, points: List[PointStruct]) -> bool:
        """
        Upsert points to collection.

        Args:
            points: List of points to upsert

        Returns:
            bool: Success status
        """
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.debug(f"Upserted {len(points)} points to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points: {e}")
            return False

    def create_document_points(
        self,
        document_id: int,
        document_number: str,
        source: str,
        title: str,
        publication_date: Optional[str],
        chunks_with_embeddings: List[tuple[str, np.ndarray]],
        hts_codes: List[str],
        agencies: List[str]
    ) -> List[PointStruct]:
        """
        Create Qdrant points for a document's chunks.

        Args:
            document_id: PostgreSQL document ID
            document_number: Document number
            source: Data source
            title: Document title
            publication_date: Publication date
            chunks_with_embeddings: List of (chunk_text, embedding) tuples
            hts_codes: List of HTS codes
            agencies: List of agency slugs

        Returns:
            List[PointStruct]: List of Qdrant points
        """
        points = []

        for chunk_index, (chunk_text, embedding) in enumerate(chunks_with_embeddings):
            payload = DocumentPayload(
                document_id=document_id,
                document_number=document_number,
                source=source,
                title=title,
                publication_date=publication_date,
                text_chunk=chunk_text,
                chunk_index=chunk_index,
                hts_codes=hts_codes,
                agencies=agencies
            )

            point = PointStruct(
                id=str(uuid4()),
                vector=embedding.tolist(),
                payload=payload.dict()
            )

            points.append(point)

        return points

    def search(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        hts_codes: Optional[List[str]] = None,
        agencies: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_vector: Query embedding
            limit: Maximum results
            score_threshold: Minimum similarity score
            hts_codes: Filter by HTS codes
            agencies: Filter by agencies
            source: Filter by source

        Returns:
            List[Dict[str, Any]]: Search results with scores
        """
        # Build filter
        query_filter = None
        conditions = []

        if hts_codes:
            for code in hts_codes:
                conditions.append(
                    FieldCondition(
                        key="hts_codes",
                        match=MatchValue(value=code)
                    )
                )

        if agencies:
            for agency in agencies:
                conditions.append(
                    FieldCondition(
                        key="agencies",
                        match=MatchValue(value=agency)
                    )
                )

        if source:
            conditions.append(
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source)
                )
            )

        if conditions:
            query_filter = Filter(must=conditions)

        # Search
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            return [
                {
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_by_document_id(self, document_id: int) -> bool:
        """
        Delete all points for a document.

        Args:
            document_id: PostgreSQL document ID

        Returns:
            bool: Success status
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.debug(f"Deleted points for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete points: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.

        Returns:
            Dict[str, Any]: Collection info
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
