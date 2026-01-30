#!/bin/bash
# Quick deployment script - Run this when Docker is available

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  US Customs Knowledge Base POC - Quick Deploy             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✓ Docker found"
echo ""

# Navigate to project
cd ~/my-new-project/customs-kb

echo "📍 Working directory: $(pwd)"
echo ""

# Start Docker services
echo "🚀 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Check services
echo ""
echo "🔍 Checking service health..."
docker-compose ps

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "🐍 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate and install
echo ""
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Initialize databases
echo ""
echo "🗄️  Initializing databases..."
python scripts/init_db.py
python scripts/init_qdrant.py

# Verify setup
echo ""
echo "✅ Verifying setup..."
python scripts/verify_setup.py

# Ingest sample data
echo ""
echo "📥 Ingesting sample HTSUS data..."
python -m src.cli.main ingest htsus

# Ask about Federal Register
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Data Ingestion Options                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Federal Register ingestion options:"
echo "  1) Quick test (last month - ~5 min)"
echo "  2) Full POC (last 2 years - ~30-60 min)"
echo "  3) Skip for now"
echo ""
read -p "Choose [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "📥 Ingesting Federal Register (last month)..."
        python -m src.cli.main ingest federal-register --start-date 2025-12-01
        ;;
    2)
        echo ""
        echo "📥 Ingesting Federal Register (last 2 years)..."
        echo "⏳ This will take 30-60 minutes..."
        python -m src.cli.main ingest federal-register
        ;;
    3)
        echo ""
        echo "⏭️  Skipping Federal Register ingestion"
        ;;
esac

# Show status
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Deployment Complete!                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
python -m src.cli.main ingest status

# Show next steps
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Try These Commands                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Activate virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "Run sample queries:"
echo "  python scripts/sample_queries.py"
echo ""
echo "Search documents:"
echo "  python -m src.cli.main query search \"cheese import rules\""
echo ""
echo "Look up HTS codes:"
echo "  python -m src.cli.main query hts-lookup \"cheese\""
echo ""
echo "Get HTS code info:"
echo "  python -m src.cli.main query hts-info 0406.30.00"
echo ""
echo "Check status anytime:"
echo "  python -m src.cli.main ingest status"
echo ""
echo "View help:"
echo "  python -m src.cli.main --help"
echo ""
echo "🎉 Happy querying!"
