#!/bin/bash
# Setup script for US Customs Knowledge Base POC

set -e

echo "=========================================="
echo "US Customs Knowledge Base - Setup"
echo "=========================================="

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✓ Python $python_version found"
else
    echo "✗ Python 3.11+ required (found $python_version)"
    exit 1
fi

# Check Docker
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
else
    echo "✗ Docker not found. Please install Docker first."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created (review and modify if needed)"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw data/processed
echo "✓ Data directories created"

# Start Docker services
echo ""
echo "Starting Docker services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U customs_user -d customs_kb > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ PostgreSQL is not ready"
fi

# Check Qdrant
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "✓ Qdrant is ready"
else
    echo "✗ Qdrant is not ready"
fi

# Initialize databases
echo ""
echo "Initializing databases..."
python scripts/init_db.py
python scripts/init_qdrant.py

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Ingest data:"
echo "     python -m src.cli.main ingest htsus"
echo "     python -m src.cli.main ingest federal-register"
echo ""
echo "  3. Try sample queries:"
echo "     python scripts/sample_queries.py"
echo ""
echo "  4. Use CLI commands:"
echo "     python -m src.cli.main query search 'cheese import rules'"
echo ""
