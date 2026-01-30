"""
Qdrant payload schemas and helper functions.
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class DocumentPayload(BaseModel):
    """Payload schema for Qdrant document points."""
    document_id: int
    document_number: str
    source: str
    title: str
    publication_date: Optional[str] = None
    text_chunk: str
    chunk_index: int
    hts_codes: List[str] = []
    agencies: List[str] = []

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }
