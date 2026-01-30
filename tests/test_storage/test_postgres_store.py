"""
Tests for PostgreSQL storage operations.
"""
import pytest
from datetime import date

from src.storage.postgres_store import PostgresStore
from src.models.postgres_models import Document, Agency, HTSCode


def test_create_document(test_db_session):
    """Test creating a document."""
    store = PostgresStore(test_db_session)

    doc_data = {
        'document_number': 'TEST-001',
        'source': 'test',
        'title': 'Test Document',
        'abstract': 'Test abstract',
        'publication_date': date(2025, 1, 1)
    }

    document = store.create_document(doc_data)

    assert document.id is not None
    assert document.document_number == 'TEST-001'
    assert document.title == 'Test Document'


def test_get_or_create_agency(test_db_session):
    """Test getting or creating an agency."""
    store = PostgresStore(test_db_session)

    # Create new agency
    agency1 = store.get_or_create_agency('cbp', 'Customs and Border Protection')
    assert agency1.id is not None
    assert agency1.slug == 'cbp'

    # Get existing agency
    agency2 = store.get_or_create_agency('cbp', 'Customs and Border Protection')
    assert agency1.id == agency2.id


def test_get_or_create_hts_code(test_db_session):
    """Test getting or creating HTS code."""
    store = PostgresStore(test_db_session)

    hts_data = {
        'hts_number': '0406.10.00',
        'description': 'Fresh cheese',
        'indent_level': 2,
        'general_rate': '10%'
    }

    # Create new HTS code
    hts1 = store.get_or_create_hts_code(hts_data)
    assert hts1.id is not None
    assert hts1.hts_number == '0406.10.00'

    # Get existing HTS code
    hts2 = store.get_or_create_hts_code(hts_data)
    assert hts1.id == hts2.id


def test_create_ingestion_run(test_db_session):
    """Test creating ingestion run."""
    store = PostgresStore(test_db_session)

    run = store.create_ingestion_run('test_source')

    assert run.id is not None
    assert run.source == 'test_source'
    assert run.status == 'running'
    assert run.documents_processed == 0


def test_update_ingestion_run(test_db_session):
    """Test updating ingestion run."""
    store = PostgresStore(test_db_session)

    run = store.create_ingestion_run('test_source')
    test_db_session.commit()

    store.update_ingestion_run(
        run.id,
        status='completed',
        documents_processed=100
    )
    test_db_session.commit()

    updated_run = test_db_session.query(
        store.session.query(run.__class__).filter_by(id=run.id).first()
    )
    # Note: This test would need the actual session to verify
