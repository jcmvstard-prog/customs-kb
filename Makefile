.PHONY: help setup start stop clean test ingest-htsus ingest-federal status query-demo

help:
	@echo "US Customs Knowledge Base - Available Commands"
	@echo "==============================================="
	@echo "setup              - Initial setup (venv, deps, Docker)"
	@echo "start              - Start Docker services"
	@echo "stop               - Stop Docker services"
	@echo "clean              - Clean up Docker volumes and data"
	@echo "test               - Run tests"
	@echo "ingest-htsus       - Ingest HTSUS data"
	@echo "ingest-federal     - Ingest Federal Register data"
	@echo "status             - Show ingestion status"
	@echo "query-demo         - Run sample queries"

setup:
	@bash setup.sh

start:
	@echo "Starting Docker services..."
	@docker-compose up -d
	@echo "Waiting for services..."
	@sleep 5
	@echo "Services started successfully"

stop:
	@echo "Stopping Docker services..."
	@docker-compose down
	@echo "Services stopped"

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@rm -rf data/raw/* data/processed/*
	@echo "Cleanup completed"

test:
	@echo "Running tests..."
	@source venv/bin/activate && pytest tests/ -v

ingest-htsus:
	@echo "Ingesting HTSUS data..."
	@source venv/bin/activate && python -m src.cli.main ingest htsus

ingest-federal:
	@echo "Ingesting Federal Register data (last 2 years)..."
	@source venv/bin/activate && python -m src.cli.main ingest federal-register

status:
	@source venv/bin/activate && python -m src.cli.main ingest status

query-demo:
	@echo "Running sample queries..."
	@source venv/bin/activate && python scripts/sample_queries.py
