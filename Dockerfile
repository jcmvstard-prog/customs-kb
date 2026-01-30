FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install production dependencies only (no dev tools, lighter PyTorch)
RUN pip install --no-cache-dir \
    click==8.1.7 \
    pydantic==2.6.0 \
    pydantic-settings==2.1.0 \
    python-dotenv==1.0.0 \
    sqlalchemy==2.0.25 \
    psycopg2-binary==2.9.9 \
    qdrant-client==1.7.0 \
    httpx==0.26.0 \
    pandas==2.1.4 \
    beautifulsoup4==4.12.3 \
    lxml==5.1.0 \
    tenacity==8.2.3 \
    tqdm==4.66.1 \
    # Lightweight ML dependencies (CPU-only PyTorch)
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.2 \
    && pip install --no-cache-dir \
    transformers==4.36.2 \
    sentence-transformers==2.3.1

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/raw data/processed

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port (if running as web service)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from src.config.database import get_db_session; session = get_db_session(); session.close()" || exit 1

# Default command - can be overridden
CMD ["python", "-m", "src.cli.main", "ingest", "status"]
