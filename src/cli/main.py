#!/usr/bin/env python
"""
Main CLI entry point.
"""
import click
from src.utils.logging_config import setup_logging


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
def cli(log_level):
    """US Customs Knowledge Base CLI."""
    setup_logging(log_level)


if __name__ == '__main__':
    # Import commands
    from src.cli.ingest_commands import ingest
    from src.cli.query_commands import query

    # Register command groups
    cli.add_command(ingest)
    cli.add_command(query)

    cli()
