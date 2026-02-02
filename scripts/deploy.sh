#!/bin/bash
# Quick deployment script for US Customs Knowledge Base

set -e

echo "🚀 US Customs Knowledge Base - Quick Deploy"
echo "==========================================="
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set your database passwords!"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after editing .env..."
fi

# Ask deployment type
echo "Choose deployment type:"
echo "1) Development (with hot-reload)"
echo "2) Production (optimized)"
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        COMPOSE_FILE="docker-compose.yml"
        echo "📦 Deploying in DEVELOPMENT mode..."
        ;;
    2)
        COMPOSE_FILE="docker-compose.production.yml"
        echo "📦 Deploying in PRODUCTION mode..."
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Build and start services
echo ""
echo "🔨 Building Docker images..."
docker-compose -f $COMPOSE_FILE build

echo ""
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🏥 Checking health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API not responding yet. Check logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs -f"
fi

# Check if data exists
echo ""
echo "📊 Checking database..."
RESPONSE=$(curl -s http://localhost:8000/api/status 2>/dev/null || echo '{"documents_count":0}')
DOC_COUNT=$(echo $RESPONSE | grep -o '"documents_count":[0-9]*' | grep -o '[0-9]*')

if [ "$DOC_COUNT" = "0" ] || [ -z "$DOC_COUNT" ]; then
    echo "⚠️  No data found in database!"
    echo ""
    echo "Choose how to populate data:"
    echo "1) Import from backup (if you have one)"
    echo "2) Ingest fresh data (takes 5-10 minutes)"
    echo "3) Skip for now"
    read -p "Enter choice [1-3]: " data_choice

    case $data_choice in
        1)
            read -p "Enter path to PostgreSQL dump file: " dump_file
            if [ -f "$dump_file" ]; then
                echo "Importing database..."
                docker-compose -f $COMPOSE_FILE exec -T postgres pg_restore -U customs_user -d customs_kb < "$dump_file"
                echo "✅ Database imported"
            else
                echo "❌ File not found: $dump_file"
            fi
            ;;
        2)
            echo "Starting data ingestion..."
            docker-compose -f $COMPOSE_FILE exec api python -m src.cli.main ingest federal-register --start-date 1994-01-01 &
            docker-compose -f $COMPOSE_FILE exec api python -m src.cli.main ingest htsus &
            echo "⏳ Ingestion started in background. Check progress:"
            echo "   docker-compose -f $COMPOSE_FILE logs -f api"
            ;;
        3)
            echo "Skipping data population. You can ingest later with:"
            echo "   docker-compose -f $COMPOSE_FILE exec api python -m src.cli.main ingest federal-register --start-date 1994-01-01"
            ;;
    esac
else
    echo "✅ Database contains $DOC_COUNT documents"
fi

# Show access info
echo ""
echo "==========================================="
echo "✅ Deployment Complete!"
echo ""
echo "Access your knowledge base:"
echo "  📡 API:       http://localhost:8000"
echo "  🌐 Dashboard: http://localhost:8000/dashboard"
echo "  📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop:         docker-compose -f $COMPOSE_FILE down"
echo "  Restart:      docker-compose -f $COMPOSE_FILE restart"
echo "  Check status: curl http://localhost:8000/api/status"
echo ""
echo "==========================================="
