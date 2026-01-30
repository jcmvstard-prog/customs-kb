#!/bin/bash
# Setup Python environment without Docker
# Docker services will need to be started separately

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  US Customs Knowledge Base - Python Setup                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd ~/my-new-project/customs-kb

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "   Found Python $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo ""
echo "📦 Installing dependencies (this may take 5-10 minutes)..."
echo "   Installing core dependencies..."
pip install -q click pydantic pydantic-settings python-dotenv
echo "   Installing database libraries..."
pip install -q sqlalchemy psycopg2-binary qdrant-client
echo "   Installing data processing..."
pip install -q pandas httpx beautifulsoup4 lxml tenacity tqdm python-dateutil
echo "   Installing ML libraries (this is the slow part)..."
pip install -q torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu
pip install -q sentence-transformers transformers
echo "   ✓ All dependencies installed"

# Download embedding model
echo ""
echo "🤖 Pre-downloading embedding model..."
python -c "from sentence_transformers import SentenceTransformer; print('Loading model...'); model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✓ Model downloaded and cached')"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Python Environment Ready!                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Virtual environment: venv/"
echo "✅ Dependencies: installed"
echo "✅ Embedding model: cached"
echo ""
echo "⏳ Still needed:"
echo "   • Docker Desktop (for PostgreSQL and Qdrant)"
echo "   • Database initialization"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Next Steps                                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Install Docker Desktop:"
echo "   https://www.docker.com/products/docker-desktop"
echo ""
echo "2. Start Docker and run:"
echo "   docker-compose up -d"
echo ""
echo "3. Initialize databases:"
echo "   python scripts/init_db.py"
echo "   python scripts/init_qdrant.py"
echo ""
echo "4. Ingest data:"
echo "   python -m src.cli.main ingest htsus"
echo "   python -m src.cli.main ingest federal-register"
echo ""
echo "5. Run queries:"
echo "   python scripts/sample_queries.py"
echo ""
