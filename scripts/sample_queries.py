#!/usr/bin/env python
"""
Sample queries for demonstrating the knowledge base.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.query.semantic_search import SemanticSearch
from src.query.structured_query import StructuredQuery
from src.query.hybrid_query import HybridQuery
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Demo queries
DEMO_QUERIES = [
    "What are the rules for importing cheese from France?",
    "Steel anti-dumping duties",
    "Textile quotas and restrictions",
    "Agricultural product sanitation requirements",
]


def run_semantic_search_demo():
    """Run semantic search demo queries."""
    print("\n" + "="*80)
    print("SEMANTIC SEARCH DEMO")
    print("="*80)

    searcher = SemanticSearch()

    for query in DEMO_QUERIES:
        print(f"\nQuery: {query}")
        print("-"*80)

        results = searcher.search(query, limit=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Document: {result['document_number']}")
            print(f"   Date: {result['publication_date']}")


def run_structured_query_demo():
    """Run structured query demo."""
    print("\n" + "="*80)
    print("STRUCTURED QUERY DEMO")
    print("="*80)

    structured = StructuredQuery()

    # HTS code lookup
    print("\n1. HTS Code Lookup: Cheese")
    print("-"*80)

    hts_results = structured.search_hts_codes("cheese", limit=5)

    for hts in hts_results:
        print(f"{hts['hts_number']}: {hts['description']}")
        print(f"  Rate: {hts['general_rate']}")


def run_hybrid_query_demo():
    """Run hybrid query demo."""
    print("\n" + "="*80)
    print("HYBRID QUERY DEMO")
    print("="*80)

    hybrid = HybridQuery()

    # Search by HTS code and text
    print("\n1. HTS 0406.30 + 'processed cheese requirements'")
    print("-"*80)

    try:
        results = hybrid.search_by_hts_and_text(
            hts_number="0406.30.00",
            query_text="processed cheese requirements",
            limit=3
        )

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Document: {result['document_number']}")

    except Exception as e:
        print(f"Note: {e}")
        print("This query requires documents with HTS code 0406.30.00 to be ingested first.")


def main():
    """Run all demo queries."""
    print("\n" + "="*80)
    print("US CUSTOMS KNOWLEDGE BASE - SAMPLE QUERIES")
    print("="*80)

    try:
        run_semantic_search_demo()
        run_structured_query_demo()
        run_hybrid_query_demo()

        print("\n" + "="*80)
        print("DEMO COMPLETED")
        print("="*80)

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\nError: {e}")
        print("\nNote: Make sure to ingest data first:")
        print("  1. Start Docker services: docker-compose up -d")
        print("  2. Initialize databases: python scripts/init_db.py && python scripts/init_qdrant.py")
        print("  3. Ingest HTSUS: python -m src.cli.main ingest htsus")
        print("  4. Ingest Federal Register: python -m src.cli.main ingest federal-register")


if __name__ == "__main__":
    main()
