# US Customs Knowledge Base

This project contains a complete US Customs and Border Protection knowledge base with 30+ years of Federal Register documents and the full HTSUS tariff schedule.

## Quick Start

**API Server:** http://localhost:8000
**Web Dashboard:** http://localhost:8000/dashboard

## Database Contents

- **Federal Register Documents:** 3,958 CBP regulations (1994-2026)
- **HTS Tariff Codes:** 29,851 complete codes (2025 edition)
- **Vector Embeddings:** 3,937 searchable chunks

## API Endpoints for Claude Code

### 1. Search Customs Documents (Semantic Search)
```bash
curl "http://localhost:8000/api/search?q=YOUR_QUERY&limit=5"
```
**Use for:** Finding regulations, rulings, notices about specific topics
**Example:** `curl "http://localhost:8000/api/search?q=steel+antidumping+duties&limit=5"`

### 2. Search HTS Tariff Codes
```bash
curl "http://localhost:8000/api/hts/search?q=PRODUCT&limit=10"
```
**Use for:** Finding tariff codes by product description
**Example:** `curl "http://localhost:8000/api/hts/search?q=cheese&limit=5"`

### 3. Get HTS Code Details
```bash
curl "http://localhost:8000/api/hts/HTS_NUMBER"
```
**Use for:** Getting duty rates for specific tariff code
**Example:** `curl "http://localhost:8000/api/hts/0406.10.00"`

### 4. Get Document Details
```bash
curl "http://localhost:8000/api/documents/DOCUMENT_NUMBER"
```
**Use for:** Getting full document text by document number
**Example:** `curl "http://localhost:8000/api/documents/2024-28582"`

### 5. System Status
```bash
curl "http://localhost:8000/api/status"
```
**Use for:** Checking database statistics and recent updates

## Helper Script

A convenience script is provided at `scripts/query_kb.sh`:

```bash
# Search documents
./scripts/query_kb.sh search "textile import quotas"

# Search HTS codes
./scripts/query_kb.sh hts "automobiles"

# Get specific HTS code
./scripts/query_kb.sh hts-detail "8703.10.00"

# Check status
./scripts/query_kb.sh status
```

## Running the Server

```bash
# Start API server
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Or use Docker Compose (starts PostgreSQL + Qdrant + API)
docker-compose up
```

## Data Ingestion

```bash
# Ingest Federal Register documents
python -m src.cli.main ingest federal-register --start-date 1994-01-01

# Ingest HTSUS tariff codes
python -m src.cli.main ingest htsus

# Check ingestion status
python -m src.cli.main ingest status
```

## Use Cases

**For Claude Code agents:**
- Answer questions about customs duties and regulations
- Find relevant CBP rulings for specific products
- Look up tariff codes and duty rates
- Research trade policy and import/export requirements
- Analyze regulatory changes over time

## Architecture

- **PostgreSQL:** Structured metadata (documents, HTS codes, relationships)
- **Qdrant:** Vector embeddings for semantic search
- **FastAPI:** REST API with 11 endpoints
- **sentence-transformers:** Local embeddings (all-MiniLM-L6-v2)

## Examples for Claude

**Q: "What are the import duties for cheese?"**
```bash
# Step 1: Find HTS codes for cheese
curl "http://localhost:8000/api/hts/search?q=cheese&limit=3"

# Step 2: Get details for specific code
curl "http://localhost:8000/api/hts/0406.10.00"

# Step 3: Search for related documents
curl "http://localhost:8000/api/search?q=cheese+import+regulations&limit=3"
```

**Q: "Show me recent CBP rulings about steel"**
```bash
curl "http://localhost:8000/api/search?q=steel+antidumping&limit=5"
```

**Q: "Find tariff codes for electronics"**
```bash
curl "http://localhost:8000/api/hts/search?q=electronics&limit=10"
```
