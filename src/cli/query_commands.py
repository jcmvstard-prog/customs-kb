"""
CLI commands for querying the knowledge base.
"""
import click
from datetime import datetime
import json

from src.query.semantic_search import SemanticSearch
from src.query.structured_query import StructuredQuery
from src.query.hybrid_query import HybridQuery
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@click.group()
def query():
    """Query commands."""
    pass


@query.command('search')
@click.argument('query_text')
@click.option('--limit', default=10, help='Maximum results')
@click.option('--score-threshold', type=float, help='Minimum similarity score')
@click.option('--hts-code', help='Filter by HTS code')
@click.option('--agency', help='Filter by agency slug')
@click.option('--source', help='Filter by source')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def search(query_text, limit, score_threshold, hts_code, agency, source, json_output):
    """
    Perform semantic search.

    Example:
        python -m src.cli.main query search "cheese import rules from France" --limit 5
    """
    try:
        searcher = SemanticSearch()

        hts_codes = [hts_code] if hts_code else None
        agencies = [agency] if agency else None

        results = searcher.search(
            query=query_text,
            limit=limit,
            score_threshold=score_threshold,
            hts_codes=hts_codes,
            agencies=agencies,
            source=source
        )

        if json_output:
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"\nFound {len(results)} results for: '{query_text}'\n")
            click.echo("="*80)

            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. {result['title']}")
                click.echo(f"   Document: {result['document_number']}")
                click.echo(f"   Score: {result['score']:.4f}")
                click.echo(f"   Date: {result['publication_date']}")
                click.echo(f"   Type: {result['document_type']}")

                if result.get('agencies'):
                    click.echo(f"   Agencies: {', '.join(result['agencies'])}")

                if result.get('hts_codes'):
                    click.echo(f"   HTS Codes: {', '.join(result['hts_codes'])}")

                click.echo(f"   URL: {result['html_url']}")
                click.echo(f"   Excerpt: {result['matched_chunk']}")
                click.echo("-"*80)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@query.command('get')
@click.argument('document_number')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def get_document(document_number, json_output):
    """
    Get document by document number.

    Example:
        python -m src.cli.main query get 2025-12345
    """
    try:
        searcher = SemanticSearch()
        document = searcher.search_by_document_number(document_number)

        if not document:
            click.echo(f"Document not found: {document_number}", err=True)
            raise click.Abort()

        if json_output:
            click.echo(json.dumps(document, indent=2))
        else:
            click.echo("\n" + "="*80)
            click.echo(f"Document: {document['document_number']}")
            click.echo("="*80)
            click.echo(f"\nTitle: {document['title']}")
            click.echo(f"Type: {document['document_type']}")
            click.echo(f"Source: {document['source']}")
            click.echo(f"Published: {document['publication_date']}")
            click.echo(f"URL: {document['html_url']}")

            if document.get('agencies'):
                click.echo("\nAgencies:")
                for agency in document['agencies']:
                    click.echo(f"  - {agency['name']} ({agency['slug']})")

            if document.get('hts_codes'):
                click.echo("\nHTS Codes:")
                for hts in document['hts_codes']:
                    click.echo(f"  - {hts['hts_number']}: {hts['description']}")
                    click.echo(f"    Rate: {hts['general_rate']}")

            click.echo(f"\nAbstract:\n{document.get('abstract', 'N/A')}")

            if document.get('full_text'):
                text = document['full_text']
                preview = text[:500] + "..." if len(text) > 500 else text
                click.echo(f"\nFull Text Preview:\n{preview}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@query.command('hts-search')
@click.argument('hts_code')
@click.argument('query_text')
@click.option('--limit', default=10, help='Maximum results')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def hts_search(hts_code, query_text, limit, json_output):
    """
    Hybrid search: HTS code + semantic query.

    Example:
        python -m src.cli.main query hts-search 0406.30 "processed cheese requirements"
    """
    try:
        hybrid = HybridQuery()
        results = hybrid.search_by_hts_and_text(
            hts_number=hts_code,
            query_text=query_text,
            limit=limit
        )

        if json_output:
            click.echo(json.dumps(results, indent=2))
        else:
            hts_info = results[0].get('hts_filter') if results else None

            if hts_info:
                click.echo(f"\nHTS Code: {hts_info['hts_number']}")
                click.echo(f"Description: {hts_info['description']}")
                click.echo(f"General Rate: {hts_info['general_rate']}")

            click.echo(f"\nFound {len(results)} results for HTS {hts_code} + '{query_text}'\n")
            click.echo("="*80)

            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. {result['title']}")
                click.echo(f"   Document: {result['document_number']}")
                click.echo(f"   Score: {result['score']:.4f}")
                click.echo(f"   Date: {result['publication_date']}")
                click.echo(f"   URL: {result['html_url']}")
                click.echo(f"   Excerpt: {result['matched_chunk']}")
                click.echo("-"*80)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@query.command('hts-info')
@click.argument('hts_code')
def hts_info(hts_code):
    """
    Get HTS code information.

    Example:
        python -m src.cli.main query hts-info 0406.30.00
    """
    try:
        structured = StructuredQuery()
        info = structured.get_hts_code_info(hts_code)

        if not info:
            click.echo(f"HTS code not found: {hts_code}", err=True)
            raise click.Abort()

        click.echo("\n" + "="*80)
        click.echo(f"HTS Code: {info['hts_number']}")
        click.echo("="*80)
        click.echo(f"Description: {info['description']}")
        click.echo(f"Indent Level: {info['indent_level']}")
        click.echo(f"General Rate: {info['general_rate']}")
        click.echo(f"Special Rate: {info['special_rate']}")

        if info.get('parent_hts_number'):
            click.echo(f"Parent: {info['parent_hts_number']}")

        click.echo(f"\nRelated Documents: {info['related_documents']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@query.command('hts-lookup')
@click.argument('search_term')
@click.option('--limit', default=20, help='Maximum results')
def hts_lookup(search_term, limit):
    """
    Search HTS codes by description.

    Example:
        python -m src.cli.main query hts-lookup "cheese"
    """
    try:
        structured = StructuredQuery()
        results = structured.search_hts_codes(search_term, limit=limit)

        click.echo(f"\nFound {len(results)} HTS codes matching '{search_term}'\n")
        click.echo("="*80)

        for result in results:
            click.echo(f"\n{result['hts_number']}: {result['description']}")
            click.echo(f"  General Rate: {result['general_rate']}")
            click.echo(f"  Special Rate: {result['special_rate']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
