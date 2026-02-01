"""
FastAPI REST API for US Customs Knowledge Base
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import date

from src.config.database import get_db_session, get_qdrant_client
from src.storage.postgres_store import PostgresStore
from src.storage.qdrant_store import QdrantStore
from src.query.semantic_search import SemanticSearch
from src.query.structured_query import StructuredQuery
from src.query.hybrid_query import HybridQuery
from src.ingest.federal_register import FederalRegisterIngester
from src.ingest.htsus import HTSUSIngester

app = FastAPI(
    title="US Customs Knowledge Base API",
    description="Hybrid search system for Federal Register documents and HTSUS tariff codes",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class HTSCode(BaseModel):
    hts_number: str
    description: str
    general_rate: Optional[str]
    special_rate: Optional[str]
    indent_level: Optional[int]
    parent_hts_number: Optional[str]

class Document(BaseModel):
    document_number: str
    title: str
    document_type: Optional[str]
    publication_date: Optional[str]
    abstract: Optional[str]
    html_url: Optional[str]

class SearchResult(BaseModel):
    document_number: str
    title: str
    score: float
    date: Optional[str]
    type: Optional[str]
    url: Optional[str]
    excerpt: Optional[str]
    agencies: List[str]

class StatusResponse(BaseModel):
    documents_count: int
    hts_codes_count: int
    vector_points: int
    recent_ingestions: List[dict]

# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "US Customs Knowledge Base API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        with get_db_session() as session:
            postgres_store = PostgresStore(session)
            doc_count = postgres_store.get_document_count()

        qdrant_client = get_qdrant_client()
        qdrant_store = QdrantStore(qdrant_client)
        collection_info = qdrant_store.get_collection_info()

        vectors_count = 0
        if collection_info:
            if hasattr(collection_info, 'points_count'):
                vectors_count = collection_info.points_count
            elif isinstance(collection_info, dict):
                vectors_count = collection_info.get('points_count', 0)

        return {
            "status": "healthy",
            "database": "connected",
            "vector_db": "connected",
            "documents": doc_count,
            "vectors": vectors_count
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# HTS Code Endpoints
@app.get("/api/hts/search", response_model=List[HTSCode])
async def search_hts_codes(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100)
):
    """Search HTS codes by keyword."""
    try:
        with get_db_session() as session:
            structured = StructuredQuery(session)
            codes = structured.search_hts_codes(q, limit=limit)

            return [
                HTSCode(
                    hts_number=code.hts_number,
                    description=code.description,
                    general_rate=code.general_rate,
                    special_rate=code.special_rate,
                    indent_level=code.indent_level,
                    parent_hts_number=code.parent_hts_number
                )
                for code in codes
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hts/{hts_number}", response_model=HTSCode)
async def get_hts_code(hts_number: str):
    """Get specific HTS code details."""
    try:
        with get_db_session() as session:
            structured = StructuredQuery(session)
            code = structured.get_hts_code(hts_number)

            if not code:
                raise HTTPException(status_code=404, detail="HTS code not found")

            return HTSCode(
                hts_number=code.hts_number,
                description=code.description,
                general_rate=code.general_rate,
                special_rate=code.special_rate,
                indent_level=code.indent_level,
                parent_hts_number=code.parent_hts_number
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Document Search Endpoints
@app.get("/api/search", response_model=List[SearchResult])
async def semantic_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=50),
    hts_code: Optional[str] = None
):
    """Semantic search across documents."""
    try:
        with get_db_session() as session:
            qdrant_client = get_qdrant_client()
            semantic = SemanticSearch(session, qdrant_client)

            filters = {}
            if hts_code:
                filters['hts_codes'] = [hts_code]

            results = semantic.search(q, limit=limit, filters=filters)

            return [
                SearchResult(
                    document_number=r['document_number'],
                    title=r['title'],
                    score=r['score'],
                    date=r['publication_date'].isoformat() if r.get('publication_date') else None,
                    type=r.get('document_type'),
                    url=r.get('html_url'),
                    excerpt=r.get('abstract', '')[:200] if r.get('abstract') else '',
                    agencies=r.get('agencies', [])
                )
                for r in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_number}", response_model=Document)
async def get_document(document_number: str):
    """Get specific document by number."""
    try:
        with get_db_session() as session:
            structured = StructuredQuery(session)
            doc = structured.get_document_by_number(document_number)

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            return Document(
                document_number=doc.document_number,
                title=doc.title,
                document_type=doc.document_type,
                publication_date=doc.publication_date.isoformat() if doc.publication_date else None,
                abstract=doc.abstract,
                html_url=doc.html_url
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Status Endpoint
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status and statistics."""
    try:
        with get_db_session() as session:
            postgres_store = PostgresStore(session)

            doc_count = postgres_store.get_document_count()
            hts_count = postgres_store.get_hts_count()
            recent_runs = postgres_store.get_recent_ingestion_runs(limit=5)

            qdrant_client = get_qdrant_client()
            qdrant_store = QdrantStore(qdrant_client)
            collection_info = qdrant_store.get_collection_info()

            vectors_count = 0
            if collection_info:
                if hasattr(collection_info, 'points_count'):
                    vectors_count = collection_info.points_count
                elif isinstance(collection_info, dict):
                    vectors_count = collection_info.get('points_count', 0)

            return StatusResponse(
                documents_count=doc_count,
                hts_codes_count=hts_count,
                vector_points=vectors_count,
                recent_ingestions=[
                    {
                        "id": run.id,
                        "source": run.source,
                        "status": run.status,
                        "documents": run.documents_processed,
                        "started_at": run.started_at.isoformat() if run.started_at else None
                    }
                    for run in recent_runs
                ]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (frontend)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/dashboard")
    async def dashboard():
        """Serve the web dashboard."""
        return FileResponse("static/index.html")
except:
    pass  # Static files not set up yet

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
