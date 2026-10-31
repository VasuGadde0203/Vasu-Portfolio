from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# text-embedding-3-small output size. The text-embedding-3 models accept a `dimensions`
# argument, so other 3-series models can be requested at this size without a schema change.
VECTOR_DIMENSIONS = 1536


class Base(DeclarativeBase):
    pass


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_document_index"),
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_project_id", "project_id"),
        Index("ix_chunks_visibility_type", "visibility", "document_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(200))
    document_title: Mapped[str] = mapped_column(String(300))
    document_type: Mapped[str] = mapped_column(String(50))
    project_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section: Mapped[str] = mapped_column(String(300))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float]] = mapped_column(Vector(VECTOR_DIMENSIONS))
    embedding_model: Mapped[str] = mapped_column(String(100))
    source_file: Mapped[str] = mapped_column(String(300))
    url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="public", server_default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # running | succeeded | failed
    embedding_model: Mapped[str] = mapped_column(String(100))
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContactMessage(Base):
    """Messages from the contact form. `client` is a hash of the visitor's address, never the raw IP."""

    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    message: Mapped[str] = mapped_column(Text)
    client: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RateLimitCounter(Base):
    """Fixed-window counters shared by every backend instance (no extra infrastructure)."""

    __tablename__ = "rate_limit_counters"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    window_start: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
