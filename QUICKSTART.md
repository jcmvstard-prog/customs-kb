# Quick Start Guide

Get the US Customs Knowledge Base POC running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- 4GB RAM
- Internet connection

## Setup Steps

### 1. Run Setup Script

```bash
cd ~/my-new-project/customs-kb
bash setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Start Docker services
- Initialize databases

### 2. Verify Setup

```bash
source venv/bin/activate
python scripts/verify_setup.py
```

All checks should pass ✓

### 3. Ingest Sample Data

```bash
# Ingest HTSUS tariff codes (sample data)
python -m src.cli.main ingest htsus

# Ingest Federal Register documents (last 2 years)
# Note: This may take 10-30 minutes depending on network speed
python -m src.cli.main ingest federal-register --start-date 2025-12-01
```

### 4. Try Sample Queries

```bash
# Run demo queries
python scripts/sample_queries.py

# Or try your own queries
python -m src.cli.main query search "cheese import regulations"
python -m src.cli.main query hts-lookup "cheese"
python -m src.cli.main query hts-info 0406.30.00
```

## Common Commands

### Ingestion
```bash
# Check ingestion status
python -m src.cli.main ingest status

# Ingest specific date range
python -m src.cli.main ingest federal-register \
    --start-date 2025-01-01 \
    --end-date 2025-12-31
```

### Queries
```bash
# Semantic search
python -m src.cli.main query search "textile import quotas" --limit 5

# Get document
python -m src.cli.main query get 2025-12345

# Hybrid search
python -m src.cli.main query hts-search 0406.30.00 "cheese regulations"

# HTS code lookup
python -m src.cli.main query hts-lookup "steel"
```

### Docker Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Using Makefile
```bash
make help           # Show all commands
make start          # Start Docker services
make stop           # Stop Docker services
make ingest-htsus   # Ingest HTSUS
make status         # Show ingestion status
make query-demo     # Run sample queries
```

## Troubleshooting

### Services won't start
```bash
docker-compose down -v
docker-compose up -d
```

### Database connection errors
```bash
# Check PostgreSQL
docker-compose logs postgres

# Check Qdrant
docker-compose logs qdrant

# Verify services are running
docker-compose ps
```

### Import errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Federal Register API timeout
```bash
# Try smaller date range
python -m src.cli.main ingest federal-register \
    --start-date 2025-12-01 \
    --end-date 2025-12-31
```

## What's Next?

1. **Explore the data**: Use CLI commands to search documents
2. **Review the code**: Check `src/` directory structure
3. **Run tests**: `pytest tests/`
4. **Extend functionality**: Add new query types, data sources, or features
5. **Build API**: Create FastAPI endpoints for web integration
6. **Add frontend**: Build a React UI for end users

## Architecture Overview

```
Federal Register API  ─┐
                       ├──> Ingestion Pipeline ──> PostgreSQL (metadata)
HTSUS Data           ─┘                      └───> Qdrant (embeddings)
                                                          │
User Query ──> CLI ──> Query Engine ─────────────────────┘
                            │
                            └──> Semantic Search (Qdrant)
                            └──> Structured Query (PostgreSQL)
                            └──> Hybrid Query (both)
```

## Need Help?

- Read the full [README.md](README.md)
- Check the implementation plan in the project root
- Review the code documentation in `src/`
- Run verification: `python scripts/verify_setup.py`
