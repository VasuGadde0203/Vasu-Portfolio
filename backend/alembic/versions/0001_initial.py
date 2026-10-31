"""Initial schema: pgvector extension, knowledge_chunks, ingestion_runs, rate_limit_counters

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Frozen here on purpose: changing the embedding size is a deliberate migration plus re-embed.
VECTOR_DIMENSIONS = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(200), nullable=False),
        sa.Column("document_title", sa.String(300), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("project_id", sa.String(100)),
        sa.Column("section", sa.String(300), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(VECTOR_DIMENSIONS), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("source_file", sa.String(300), nullable=False),
        sa.Column("url", sa.String(300)),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="public"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunk_document_index"),
    )
    op.create_index("ix_chunks_document_id", "knowledge_chunks", ["document_id"])
    op.create_index("ix_chunks_project_id", "knowledge_chunks", ["project_id"])
    op.create_index("ix_chunks_visibility_type", "knowledge_chunks", ["visibility", "document_type"])
    # No vector index: the corpus is tens of chunks, so an exact scan is fast and exact.
    # If it grows past a few thousand chunks, add:
    #   CREATE INDEX ... USING hnsw (embedding vector_cosine_ops);

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("stats", postgresql.JSONB),
        sa.Column("error", sa.Text),
    )

    op.create_table(
        "rate_limit_counters",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("window_start", sa.BigInteger, primary_key=True),
        sa.Column("count", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("rate_limit_counters")
    op.drop_table("ingestion_runs")
    op.drop_table("knowledge_chunks")
