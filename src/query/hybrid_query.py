"""
Hybrid queries combining semantic and structured search.
"""
from typing import List, Dict, Any, Optional
from datetime import date

from src.query.semantic_search import SemanticSearch
from src.query.structured_query import StructuredQuery
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HybridQuery:
    """Hybrid query combining semantic and structured search."""

    def __init__(self):
        """Initialize hybrid query."""
        self.semantic_search = SemanticSearch()
        self.structured_query = StructuredQuery()

    def search_by_hts_and_text(
        self,
        hts_number: str,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents by HTS code and semantic relevance.

        Args:
            hts_number: HTS code to filter by
            query_text: Semantic search query
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List[Dict[str, Any]]: Ranked results
        """
        logger.info(f"Hybrid search: HTS {hts_number} + query '{query_text}'")

        # Semantic search with HTS filter
        results = self.semantic_search.search(
            query=query_text,
            limit=limit,
            score_threshold=score_threshold,
            hts_codes=[hts_number]
        )

        # Enrich with HTS code information
        hts_info = self.structured_query.get_hts_code_info(hts_number)

        for result in results:
            result['hts_filter'] = hts_info

        return results

    def search_with_date_filter(
        self,
        query_text: str,
        start_date: date,
        end_date: date,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with date range filter.

        Args:
            query_text: Search query
            start_date: Start date
            end_date: End date
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List[Dict[str, Any]]: Ranked results
        """
        logger.info(f"Hybrid search with date filter: {start_date} to {end_date}")

        # Get documents in date range
        date_filtered_docs = self.structured_query.search_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=1000  # Get larger set for semantic filtering
        )

        document_numbers = [doc['document_number'] for doc in date_filtered_docs]

        # Perform semantic search
        semantic_results = self.semantic_search.search(
            query=query_text,
            limit=limit * 2,  # Get more results for filtering
            score_threshold=score_threshold
        )

        # Filter semantic results to only include date-filtered documents
        filtered_results = [
            result for result in semantic_results
            if result['document_number'] in document_numbers
        ]

        return filtered_results[:limit]

    def search_by_agency_and_text(
        self,
        agency_slug: str,
        query_text: str,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents by agency and semantic relevance.

        Args:
            agency_slug: Agency slug to filter by
            query_text: Semantic search query
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List[Dict[str, Any]]: Ranked results
        """
        logger.info(f"Hybrid search: Agency {agency_slug} + query '{query_text}'")

        # Semantic search with agency filter
        results = self.semantic_search.search(
            query=query_text,
            limit=limit,
            score_threshold=score_threshold,
            agencies=[agency_slug]
        )

        return results

    def multi_filter_search(
        self,
        query_text: str,
        hts_codes: Optional[List[str]] = None,
        agencies: Optional[List[str]] = None,
        source: Optional[str] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with multiple filters.

        Args:
            query_text: Search query
            hts_codes: Filter by HTS codes
            agencies: Filter by agencies
            source: Filter by source
            limit: Maximum results
            score_threshold: Minimum similarity score

        Returns:
            List[Dict[str, Any]]: Ranked results
        """
        logger.info(f"Multi-filter search with {len(hts_codes or [])} HTS codes, {len(agencies or [])} agencies")

        results = self.semantic_search.search(
            query=query_text,
            limit=limit,
            score_threshold=score_threshold,
            hts_codes=hts_codes,
            agencies=agencies,
            source=source
        )

        return results
