"""
SQLAlchemy ORM models for PostgreSQL database.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    ForeignKey, Table, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association Tables
document_agencies = Table(
    'document_agencies',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('agency_id', Integer, ForeignKey('agencies.id', ondelete='CASCADE'), primary_key=True)
)

document_hts_codes = Table(
    'document_hts_codes',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('hts_code_id', Integer, ForeignKey('hts_codes.id', ondelete='CASCADE'), primary_key=True)
)


class Document(Base):
    """Core document metadata."""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    document_number = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    document_type = Column(String(100))
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    publication_date = Column(Date, index=True)
    html_url = Column(Text)
    full_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    agencies = relationship('Agency', secondary=document_agencies, back_populates='documents')
    hts_codes = relationship('HTSCode', secondary=document_hts_codes, back_populates='documents')

    def __repr__(self):
        return f"<Document(document_number='{self.document_number}', title='{self.title[:50]}...')>"


class Agency(Base):
    """Government agencies."""
    __tablename__ = 'agencies'

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Relationships
    documents = relationship('Document', secondary=document_agencies, back_populates='agencies')

    def __repr__(self):
        return f"<Agency(slug='{self.slug}', name='{self.name}')>"


class HTSCode(Base):
    """Harmonized Tariff Schedule codes."""
    __tablename__ = 'hts_codes'

    id = Column(Integer, primary_key=True)
    hts_number = Column(String(50), unique=True, nullable=False, index=True)
    indent_level = Column(Integer)
    description = Column(Text, nullable=False)
    general_rate = Column(Text)  # Changed from String(200) to Text for long descriptions
    special_rate = Column(Text)  # Changed from String(200) to Text for long descriptions
    parent_hts_number = Column(String(50))
    effective_date = Column(Date)

    # Relationships
    documents = relationship('Document', secondary=document_hts_codes, back_populates='hts_codes')

    def __repr__(self):
        return f"<HTSCode(hts_number='{self.hts_number}', description='{self.description[:50]}...')>"


class IngestionRun(Base):
    """Track ingestion jobs."""
    __tablename__ = 'ingestion_runs'

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    documents_processed = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    def __repr__(self):
        return f"<IngestionRun(source='{self.source}', status='{self.status}', docs={self.documents_processed})>"


# Create indexes
Index('idx_document_number', Document.document_number)
Index('idx_publication_date', Document.publication_date)
Index('idx_hts_number', HTSCode.hts_number)
Index('idx_agency_slug', Agency.slug)
