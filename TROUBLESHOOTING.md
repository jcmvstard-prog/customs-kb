# Troubleshooting Guide

Common issues and solutions for the US Customs Knowledge Base POC.

## Setup Issues

### Docker services won't start

**Symptom**: `docker-compose up -d` fails or services show as unhealthy

**Solutions**:
```bash
# 1. Clean up and restart
docker-compose down -v
docker-compose up -d

# 2. Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant

# 3. View logs
docker-compose logs postgres
docker-compose logs qdrant

# 4. Check disk space
df -h

# 5. Restart Docker Desktop (if on Mac/Windows)
```

### Virtual environment activation fails

**Symptom**: `source venv/bin/activate` doesn't work

**Solutions**:
```bash
# 1. Recreate virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate

# 2. On Windows, use:
venv\Scripts\activate

# 3. Verify Python version
python --version  # Should be 3.11+
```

### Dependency installation errors

**Symptom**: `pip install -r requirements.txt` fails

**Solutions**:
```bash
# 1. Upgrade pip
pip install --upgrade pip

# 2. Install one at a time to find the culprit
pip install pydantic
pip install sqlalchemy
# ... etc

# 3. Check for system dependencies
# On Ubuntu/Debian:
sudo apt-get install python3-dev libpq-dev

# On macOS:
brew install postgresql

# 4. Use specific versions if needed
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu
```

## Database Issues

### PostgreSQL connection refused

**Symptom**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# 1. Check if PostgreSQL is running
docker-compose ps

# 2. Restart PostgreSQL
docker-compose restart postgres

# 3. Check connection parameters in .env
cat .env | grep POSTGRES

# 4. Test connection manually
docker-compose exec postgres psql -U customs_user -d customs_kb

# 5. Check logs
docker-compose logs postgres | tail -50
```

### Qdrant connection errors

**Symptom**: `QdrantException: Connection refused`

**Solutions**:
```bash
# 1. Check if Qdrant is running
curl http://localhost:6333/health

# 2. Restart Qdrant
docker-compose restart qdrant

# 3. Check logs
docker-compose logs qdrant

# 4. Verify collection exists
curl http://localhost:6333/collections/cbp_documents

# 5. Recreate collection if needed
python scripts/init_qdrant.py
```

### Database tables not created

**Symptom**: `sqlalchemy.exc.ProgrammingError: relation does not exist`

**Solutions**:
```bash
# 1. Run initialization script
python scripts/init_db.py

# 2. Check tables exist
docker-compose exec postgres psql -U customs_user -d customs_kb -c "\dt"

# 3. Drop and recreate if needed
docker-compose down -v
docker-compose up -d
python scripts/init_db.py
python scripts/init_qdrant.py
```

## Ingestion Issues

### Federal Register API timeout

**Symptom**: `httpx.ReadTimeout` or very slow ingestion

**Solutions**:
```bash
# 1. Use smaller date range
python -m src.cli.main ingest federal-register \
    --start-date 2025-12-01 \
    --end-date 2025-12-31

# 2. Check internet connection
curl https://www.federalregister.gov/api/v1/documents?per_page=1

# 3. Increase timeout in settings (edit .env)
# Add: TIMEOUT=60

# 4. Try again during off-peak hours
```

### Embedding model download fails

**Symptom**: Model download hangs or fails during first run

**Solutions**:
```bash
# 1. Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# 2. Check disk space
df -h

# 3. Use different model cache location
export SENTENCE_TRANSFORMERS_HOME=/path/to/large/disk

# 4. Check Hugging Face status
curl https://huggingface.co/
```

### Out of memory during embedding

**Symptom**: `RuntimeError: CUDA out of memory` or Python killed

**Solutions**:
```bash
# 1. Reduce batch size in .env
BATCH_SIZE=8  # Instead of 32

# 2. Use CPU-only (default in POC)
# Model automatically uses CPU if CUDA unavailable

# 3. Process fewer documents at once
python -m src.cli.main ingest federal-register \
    --start-date 2025-12-15 \
    --end-date 2025-12-31

# 4. Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory
```

### Ingestion stuck or hanging

**Symptom**: Ingestion process stops responding

**Solutions**:
```bash
# 1. Check logs
docker-compose logs -f

# 2. Check ingestion status
python -m src.cli.main ingest status

# 3. Kill and restart
# Find process: ps aux | grep python
# Kill: kill <PID>

# 4. Clear partial data and restart
docker-compose restart postgres qdrant
python scripts/init_db.py
python scripts/init_qdrant.py
```

## Query Issues

### No results returned

**Symptom**: Search returns empty results

**Solutions**:
```bash
# 1. Check if data was ingested
python -m src.cli.main ingest status

# 2. Verify documents exist
docker-compose exec postgres psql -U customs_user -d customs_kb \
    -c "SELECT COUNT(*) FROM documents;"

# 3. Check Qdrant has vectors
curl http://localhost:6333/collections/cbp_documents

# 4. Lower score threshold
python -m src.cli.main query search "test" --score-threshold 0.1

# 5. Try broader query
python -m src.cli.main query search "import" --limit 10
```

### Import errors in CLI

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solutions**:
```bash
# 1. Ensure virtual environment is activated
source venv/bin/activate

# 2. Check you're in project root
pwd  # Should be .../customs-kb

# 3. Reinstall package in editable mode
pip install -e .

# 4. Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Slow query performance

**Symptom**: Queries take >5 seconds

**Solutions**:
```bash
# 1. Reduce result limit
python -m src.cli.main query search "test" --limit 5

# 2. Check database indexes
docker-compose exec postgres psql -U customs_user -d customs_kb \
    -c "\d documents"

# 3. Check Qdrant collection size
curl http://localhost:6333/collections/cbp_documents

# 4. Restart services to clear caches
docker-compose restart

# 5. Use structured query for known document IDs
python -m src.cli.main query get <document-number>
```

## Development Issues

### Tests failing

**Symptom**: `pytest` shows test failures

**Solutions**:
```bash
# 1. Check test database connection
pytest tests/ -v -s

# 2. Run specific test
pytest tests/test_utils/test_text_processing.py -v

# 3. Check fixtures
pytest --fixtures

# 4. Clear pytest cache
rm -rf .pytest_cache
pytest tests/

# 5. Reinstall test dependencies
pip install pytest pytest-cov pytest-asyncio
```

### Import errors in development

**Symptom**: IDE shows import errors but code runs

**Solutions**:
```bash
# 1. Configure IDE Python interpreter
# Point to venv/bin/python

# 2. Mark src as sources root (PyCharm/VSCode)

# 3. Restart IDE

# 4. Check .vscode/settings.json or .idea config
```

## Performance Issues

### High memory usage

**Symptom**: System slows down, OOM errors

**Solutions**:
```bash
# 1. Reduce batch size
# Edit .env: BATCH_SIZE=8

# 2. Process smaller chunks
# Edit .env: CHUNK_SIZE=256

# 3. Limit concurrent operations
# Process fewer documents at once

# 4. Increase Docker memory
# Docker Desktop -> Resources -> Memory

# 5. Monitor memory usage
docker stats
```

### Disk space running out

**Symptom**: "No space left on device" errors

**Solutions**:
```bash
# 1. Check disk usage
df -h
du -sh ~/my-new-project/customs-kb/*

# 2. Clean Docker volumes
docker system prune -a --volumes

# 3. Clear data directory
rm -rf data/raw/*
rm -rf data/processed/*

# 4. Remove old models cache
rm -rf ~/.cache/torch/sentence_transformers/

# 5. Use external storage for data
# Edit docker-compose.yml to use external volume
```

## Common Error Messages

### "Collection not found"
```bash
python scripts/init_qdrant.py
```

### "Table doesn't exist"
```bash
python scripts/init_db.py
```

### "Connection refused"
```bash
docker-compose up -d
sleep 10  # Wait for services to start
```

### "Permission denied"
```bash
chmod +x setup.sh scripts/*.py
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Getting Help

### Check Status
```bash
# 1. Run verification
python scripts/verify_setup.py

# 2. Check all services
docker-compose ps
docker-compose logs

# 3. Check ingestion status
python -m src.cli.main ingest status
```

### Collect Debug Information
```bash
# System info
uname -a
python --version
docker --version

# Service status
docker-compose ps
docker-compose logs --tail=100

# Database status
docker-compose exec postgres psql -U customs_user -d customs_kb -c "\dt"
curl http://localhost:6333/collections

# Ingestion status
python -m src.cli.main ingest status
```

### Reset Everything
```bash
# Nuclear option - complete reset
docker-compose down -v
rm -rf venv data/
bash setup.sh
```

## Still Having Issues?

1. Check the [README.md](README.md) for setup instructions
2. Review [QUICKSTART.md](QUICKSTART.md) for step-by-step guide
3. Run verification: `python scripts/verify_setup.py`
4. Check Docker logs: `docker-compose logs`
5. Verify environment: `cat .env`

## Useful Commands Reference

```bash
# Setup
bash setup.sh
python scripts/verify_setup.py

# Docker
docker-compose up -d
docker-compose down
docker-compose ps
docker-compose logs -f

# Ingestion
python -m src.cli.main ingest htsus
python -m src.cli.main ingest federal-register
python -m src.cli.main ingest status

# Queries
python -m src.cli.main query search "text"
python -m src.cli.main query get <doc-id>
python -m src.cli.main query hts-lookup "keyword"

# Testing
pytest tests/ -v
python scripts/sample_queries.py

# Maintenance
docker system prune -a
rm -rf data/raw/* data/processed/*
```
