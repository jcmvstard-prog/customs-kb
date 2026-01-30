"""
CLI commands for data ingestion.
"""
import click
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from src.ingest.federal_register import FederalRegisterIngester
from src.ingest.htsus import HTSUSIngester
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@click.group()
def ingest():
    """Data ingestion commands."""
    pass


@ingest.command('federal-register')
@click.option(
    '--start-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Start date (YYYY-MM-DD). Defaults to 2 years ago.'
)
@click.option(
    '--end-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='End date (YYYY-MM-DD). Defaults to today.'
)
def federal_register(start_date, end_date):
    """
    Ingest Federal Register documents.

    Example:
        python -m src.cli.main ingest federal-register --start-date 2025-01-01 --end-date 2025-12-31
    """
    # Default dates
    if not end_date:
        end_date = datetime.now()

    if not start_date:
        # Default to 2 years ago for POC
        start_date = end_date - relativedelta(years=2)

    start = start_date.date() if hasattr(start_date, 'date') else start_date
    end = end_date.date() if hasattr(end_date, 'date') else end_date

    click.echo(f"Ingesting Federal Register documents from {start} to {end}")

    try:
        ingester = FederalRegisterIngester()
        stats = ingester.run(start_date=start, end_date=end)

        click.echo("\n" + "="*50)
        click.echo("Ingestion completed!")
        click.echo(f"Status: {stats['status']}")
        click.echo(f"Documents processed: {stats['records_processed']}")
        click.echo(f"Duration: {stats['duration_seconds']:.2f} seconds")

        if stats.get('errors'):
            click.echo(f"Errors: {len(stats['errors'])}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ingest.command('htsus')
@click.option(
    '--url',
    help='URL to download HTSUS data from (optional)'
)
def htsus(url):
    """
    Ingest HTSUS tariff codes.

    Example:
        python -m src.cli.main ingest htsus
    """
    click.echo("Ingesting HTSUS tariff data")

    try:
        ingester = HTSUSIngester()
        stats = ingester.run(url=url)

        click.echo("\n" + "="*50)
        click.echo("Ingestion completed!")
        click.echo(f"Status: {stats['status']}")
        click.echo(f"HTS codes processed: {stats['records_processed']}")
        click.echo(f"Duration: {stats['duration_seconds']:.2f} seconds")

        if stats.get('errors'):
            click.echo(f"Errors: {len(stats['errors'])}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@ingest.command('status')
def status():
    """Show ingestion status and statistics."""
    from src.config.database import get_db_session, get_qdrant_client
    from src.storage.qdrant_store import QdrantStore
    from src.models.postgres_models import Document, HTSCode, IngestionRun
    from sqlalchemy import func

    try:
        with get_db_session() as db_session:
            # PostgreSQL stats
            doc_count = db_session.query(func.count(Document.id)).scalar()
            hts_count = db_session.query(func.count(HTSCode.id)).scalar()

            # Recent ingestion runs
            recent_runs = db_session.query(IngestionRun).order_by(
                IngestionRun.started_at.desc()
            ).limit(5).all()

            click.echo("="*50)
            click.echo("DATABASE STATISTICS")
            click.echo("="*50)
            click.echo(f"Documents: {doc_count}")
            click.echo(f"HTS Codes: {hts_count}")

            # Qdrant stats
            qdrant_client = get_qdrant_client()
            qdrant_store = QdrantStore(qdrant_client)
            qdrant_info = qdrant_store.get_collection_info()

            click.echo(f"\nQdrant Collection: {qdrant_info.get('name', 'N/A')}")
            click.echo(f"Vector Points: {qdrant_info.get('points_count', 0)}")

            click.echo("\n" + "="*50)
            click.echo("RECENT INGESTION RUNS")
            click.echo("="*50)

            for run in recent_runs:
                click.echo(f"\nID: {run.id}")
                click.echo(f"Source: {run.source}")
                click.echo(f"Status: {run.status}")
                click.echo(f"Documents: {run.documents_processed}")
                click.echo(f"Started: {run.started_at}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
