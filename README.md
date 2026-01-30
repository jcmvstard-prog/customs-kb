# US Customs Knowledge Base POC

A hybrid knowledge base system combining semantic search (Qdrant) with structured lookups (PostgreSQL) for US Customs and Border Protection data.

## Features

- **Hybrid Search**: Combines vector similarity search with structured SQL queries
- **Federal Register Integration**: Ingest CBP regulations, rulings, and notices
- **HTSUS Support**: Harmonized Tariff Schedule codes with duty rates
- **Semantic Search**: Natural language queries powered by sentence-transformers
- **CLI Interface**: Easy-to-use command-line tools for ingestion and querying

## Architecture

### Data Sources
- **Federal Register API**: CBP documents (1994-present)
- **HTSUS**: Tariff codes and duty rates

### Storage
- **PostgreSQL**: Document metadata, agencies, HTS codes
- **Qdrant**: Vector embeddings for semantic search
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- 4GB RAM minimum

### Installation

```bash
# 1. Navigate to project directory
cd ~/my-new-project/customs-kb

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# 5. Start Docker services
docker-compose up -d

# Wait for services to be ready (check with docker-compose ps)

# 6. Initialize databases
python scripts/init_db.py
python scripts/init_qdrant.py
```

### Data Ingestion

```bash
# Ingest HTSUS tariff codes (sample data for POC)
python -m src.cli.main ingest htsus

# Ingest Federal Register documents (last 2 years by default)
python -m src.cli.main ingest federal-register

# Or specify date range
python -m src.cli.main ingest federal-register \
    --start-date 2025-01-01 \
    --end-date 2025-12-31

# Check ingestion status
python -m src.cli.main ingest status
```

### Querying

#### Semantic Search
```bash
# Basic semantic search
python -m src.cli.main query search "cheese import rules from France" --limit 5

# With filters
python -m src.cli.main query search "textile regulations" \
    --hts-code 6204.11.00 \
    --limit 10
```

#### Get Document by Number
```bash
python -m src.cli.main query get 2025-12345
```

#### HTS Code Queries
```bash
# Search HTS codes
python -m src.cli.main query hts-lookup "cheese"

# Get HTS code details
python -m src.cli.main query hts-info 0406.30.00

# Hybrid search: HTS code + semantic query
python -m src.cli.main query hts-search 0406.30.00 "processed cheese requirements"
```

#### Run Demo Queries
```bash
python scripts/sample_queries.py
```

## Project Structure

```
customs-kb/
├── docker-compose.yml          # PostgreSQL + Qdrant services
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── README.md
│
├── src/
│   ├── config/                 # Settings and database connections
│   ├── models/                 # ORM models and schemas
│   ├── ingest/                 # Data ingestion pipelines
│   ├── storage/                # Database operations
│   ├── query/                  # Search interfaces
│   ├── utils/                  # Utilities (logging, retry, text processing)
│   └── cli/                    # Command-line interface
│
├── scripts/
│   ├── init_db.py              # Initialize PostgreSQL
│   ├── init_qdrant.py          # Initialize Qdrant
│   └── sample_queries.py       # Demo queries
│
├── tests/                      # Unit and integration tests
└── data/                       # Data directory (gitignored)
    ├── raw/                    # Downloaded files
    └── processed/              # Processed data
```

## Database Schemas

### PostgreSQL Tables

- **documents**: Core document metadata (document_number, title, abstract, full_text)
- **agencies**: Government agencies (slug, name)
- **hts_codes**: Tariff codes (hts_number, description, rates)
- **document_agencies**: Many-to-many relationship
- **document_hts_codes**: Many-to-many relationship
- **ingestion_runs**: Track ingestion jobs

### Qdrant Collection

- **Collection**: cbp_documents
- **Vector Size**: 384 (sentence-transformers)
- **Distance**: Cosine similarity
- **Payload**: document_id, title, text_chunk, HTS codes, agencies

## CLI Commands

### Ingestion

```bash
# Ingest Federal Register documents
python -m src.cli.main ingest federal-register [OPTIONS]

# Ingest HTSUS tariff codes
python -m src.cli.main ingest htsus

# Check ingestion status
python -m src.cli.main ingest status
```

### Queries

```bash
# Semantic search
python -m src.cli.main query search QUERY [OPTIONS]

# Get document by number
python -m src.cli.main query get DOCUMENT_NUMBER

# Hybrid search with HTS filter
python -m src.cli.main query hts-search HTS_CODE QUERY

# HTS code lookup
python -m src.cli.main query hts-lookup SEARCH_TERM

# HTS code information
python -m src.cli.main query hts-info HTS_CODE
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

### Code Formatting

```bash
pip install black
black src/ scripts/ tests/
```

## Configuration

Environment variables (see `.env.example`):

- **PostgreSQL**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **Qdrant**: `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION`
- **Embedding**: `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `CHUNK_SIZE`, `CHUNK_OVERLAP`
- **Federal Register**: `FEDERAL_REGISTER_BASE_URL`, `FEDERAL_REGISTER_AGENCY`
- **Ingestion**: `BATCH_SIZE`, `MAX_RETRIES`, `RETRY_DELAY`

## Performance

### POC Targets
- **Semantic search**: <500ms (P95) for 10k documents
- **Ingestion rate**: >100 docs/minute
- **Embedding generation**: <1s per batch of 32 docs

## Example Queries

```python
from src.query.semantic_search import SemanticSearch
from src.query.hybrid_query import HybridQuery

# Semantic search
searcher = SemanticSearch()
results = searcher.search("cheese import regulations", limit=5)

# Hybrid search
hybrid = HybridQuery()
results = hybrid.search_by_hts_and_text(
    hts_number="0406.30.00",
    query_text="processed cheese requirements",
    limit=10
)
```

## Troubleshooting

### Docker services not starting
```bash
docker-compose down
docker-compose up -d
docker-compose ps  # Check status
```

### Database connection errors
```bash
# Check PostgreSQL
docker-compose logs postgres

# Check Qdrant
docker-compose logs qdrant
```

### Ingestion fails
```bash
# Check logs
python -m src.cli.main ingest status

# Verify network connectivity
curl https://www.federalregister.gov/api/v1/documents?per_page=1
```

## Future Enhancements

- Additional data sources (CBP CROSS rulings, Weekly Customs Bulletins)
- FastAPI REST API
- React frontend
- Real-time updates via webhooks
- Question answering model (BERT/T5)
- Kubernetes deployment

## License

POC for evaluation purposes.

## Contact

For questions or issues, please contact the project team.
