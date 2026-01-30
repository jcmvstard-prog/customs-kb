#!/usr/bin/env python
"""
Verify system setup and configuration.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import inspect

from src.config.database import engine, get_qdrant_client
from src.config.settings import settings
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python version {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        return False


def check_postgres():
    """Check PostgreSQL connection."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ PostgreSQL connected ({len(tables)} tables)")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False


def check_qdrant():
    """Check Qdrant connection."""
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        print(f"✓ Qdrant connected ({len(collections)} collections)")
        return True
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")
        return False


def check_federal_register_api():
    """Check Federal Register API accessibility."""
    try:
        url = f"{settings.federal_register_base_url}/documents"
        params = {'per_page': 1}

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

        print("✓ Federal Register API accessible")
        return True
    except Exception as e:
        print(f"✗ Federal Register API check failed: {e}")
        return False


def check_embedding_model():
    """Check if embedding model can be loaded."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.embedding_model)
        test_embedding = model.encode("test")

        if len(test_embedding) == settings.embedding_dimension:
            print(f"✓ Embedding model loaded ({settings.embedding_model})")
            return True
        else:
            print(f"✗ Embedding dimension mismatch: expected {settings.embedding_dimension}, got {len(test_embedding)}")
            return False
    except Exception as e:
        print(f"✗ Embedding model load failed: {e}")
        return False


def check_data_directories():
    """Check data directories exist."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    if raw_dir.exists() and processed_dir.exists():
        print("✓ Data directories exist")
        return True
    else:
        print("✗ Data directories missing")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("US Customs Knowledge Base - Setup Verification")
    print("="*60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("PostgreSQL", check_postgres),
        ("Qdrant", check_qdrant),
        ("Federal Register API", check_federal_register_api),
        ("Embedding Model", check_embedding_model),
        ("Data Directories", check_data_directories),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {name} check failed with error: {e}")
            results.append(False)
        print()

    print("="*60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ All checks passed ({passed}/{total})")
        print()
        print("System is ready! Next steps:")
        print("  1. Ingest HTSUS data: python -m src.cli.main ingest htsus")
        print("  2. Ingest Federal Register: python -m src.cli.main ingest federal-register")
        print("  3. Run sample queries: python scripts/sample_queries.py")
        return 0
    else:
        print(f"✗ Some checks failed ({passed}/{total} passed)")
        print()
        print("Please fix the issues above and run this script again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
