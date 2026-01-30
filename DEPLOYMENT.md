# Deployment Guide

## Current Status

✅ **All code implemented and ready**
✅ **Configuration files created**
✅ **Environment file (.env) configured**
⏳ **Awaiting Docker services to start**

## Deployment Steps

### Step 1: Start Docker Desktop

Ensure Docker Desktop is running on your Mac:
```bash
# Check if Docker is running
docker --version
docker-compose --version
```

If Docker is not installed, download from: https://www.docker.com/products/docker-desktop

### Step 2: Navigate to Project

```bash
cd ~/my-new-project/customs-kb
```

### Step 3: Start Services (5 minutes)

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
docker-compose ps
```

Expected output:
```
NAME                      STATUS    PORTS
customs_kb_postgres       Up        0.0.0.0:5432->5432/tcp
customs_kb_qdrant         Up        0.0.0.0:6333->6333/tcp
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (may take 5-10 minutes for ML libraries)
pip install -r requirements.txt
```

### Step 5: Initialize Databases

```bash
# Create PostgreSQL tables
python scripts/init_db.py

# Create Qdrant collection
python scripts/init_qdrant.py
```

Expected output:
```
Creating database tables...
Database tables created successfully
Created tables: documents, agencies, hts_codes, ...

Creating Qdrant collection: cbp_documents
Collection 'cbp_documents' created successfully
```

### Step 6: Verify Setup

```bash
python scripts/verify_setup.py
```

All checks should pass with ✓

### Step 7: Ingest Sample Data (2-5 minutes)

```bash
# Ingest HTSUS tariff codes (fast - sample data)
python -m src.cli.main ingest htsus

# Ingest Federal Register documents (slower - API calls)
# Start with last month for quick testing:
python -m src.cli.main ingest federal-register \
    --start-date 2025-12-01 \
    --end-date 2025-12-31
```

### Step 8: Test Queries

```bash
# Check ingestion status
python -m src.cli.main ingest status

# Try semantic search
python -m src.cli.main query search "cheese import regulations" --limit 5

# Look up HTS codes
python -m src.cli.main query hts-lookup "cheese"

# Get HTS code details
python -m src.cli.main query hts-info 0406.30.00

# Run demo queries
python scripts/sample_queries.py
```

## Alternative: One-Command Deployment

If you prefer automated setup:

```bash
cd ~/my-new-project/customs-kb
bash setup.sh
```

This script will:
1. ✅ Check Python version
2. ✅ Create virtual environment
3. ✅ Install dependencies
4. ✅ Start Docker services
5. ✅ Initialize databases
6. ✅ Verify setup

## Using Makefile Commands

For convenience, use the Makefile:

```bash
# Show all available commands
make help

# Start Docker services
make start

# Ingest data
make ingest-htsus
make ingest-federal

# Check status
make status

# Run demo queries
make query-demo

# Stop services
make stop

# Complete cleanup
make clean
```

## Verification Checklist

After deployment, verify:

- [ ] Docker containers running: `docker-compose ps`
- [ ] PostgreSQL accessible: `docker-compose exec postgres psql -U customs_user -d customs_kb -c "\dt"`
- [ ] Qdrant accessible: `curl http://localhost:6333/health`
- [ ] Virtual environment active: `which python` shows venv path
- [ ] Dependencies installed: `pip list | grep sentence-transformers`
- [ ] Tables created: `python scripts/verify_setup.py`
- [ ] Data ingested: `python -m src.cli.main ingest status`
- [ ] Queries working: `python -m src.cli.main query search "test"`

## Troubleshooting

If you encounter issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Common fixes:
```bash
# Reset everything
docker-compose down -v
rm -rf venv data/
bash setup.sh

# Check logs
docker-compose logs -f

# Verify setup
python scripts/verify_setup.py
```

## System Requirements

- **Python**: 3.11+
- **Docker**: Latest version
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space
- **Network**: Internet connection for API access and model downloads

## Expected Timing

- **Setup**: 10-15 minutes (first time)
- **HTSUS ingestion**: 1 minute
- **Federal Register (1 month)**: 5-10 minutes
- **Federal Register (2 years)**: 30-60 minutes
- **Query response**: <500ms

## Next Steps After Deployment

1. **Test all query types**:
   - Semantic: Natural language search
   - Structured: Document lookup by ID
   - Hybrid: HTS code + semantic search

2. **Explore the data**:
   - Browse ingested documents
   - Check HTS code relationships
   - Review agency connections

3. **Performance testing**:
   - Measure query latency
   - Test with larger datasets
   - Monitor resource usage

4. **Extend functionality**:
   - Add more data sources
   - Build REST API
   - Create web frontend
   - Add authentication

## Production Deployment

For production use:
1. Use managed PostgreSQL (AWS RDS, Cloud SQL)
2. Use managed Qdrant (Qdrant Cloud)
3. Add authentication and RBAC
4. Set up monitoring (Prometheus, Grafana)
5. Configure backups
6. Use Kubernetes for orchestration
7. Add rate limiting and caching

## Support

- Documentation: See README.md, QUICKSTART.md
- Troubleshooting: See TROUBLESHOOTING.md
- Code: Review src/ directory
- Tests: Run `pytest tests/`

---

**Ready to deploy!** Run `bash setup.sh` when Docker is available.
