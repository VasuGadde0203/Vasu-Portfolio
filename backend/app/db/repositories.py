from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import IngestionRun, KnowledgeChunk, RateLimitCounter


@dataclass(frozen=True)
class ScoredChunk:
    document_id: str
    document_title: str
    document_type: str
    project_id: str | None
    section: str
    chunk_index: int
    content: str
    content_hash: str
    url: str | None
    score: float  # cosine similarity in [-1, 1]; higher is more similar


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ---- retrieval -------------------------------------------------------------------------
    def search(
        self,
        embedding: Sequence[float],
        *,
        embedding_model: str,
        limit: int,
        project_id: str | None = None,
        document_types: Sequence[str] | None = None,
    ) -> list[ScoredChunk]:
        """Exact cosine-similarity search over public chunks embedded with the given model.

        The knowledge base is small (tens of chunks), so an exact scan is both faster to build
        and more accurate than an approximate index. Add HNSW only if the corpus grows large.
        """
        distance = KnowledgeChunk.embedding.cosine_distance(list(embedding))
        stmt = (
            select(KnowledgeChunk, (1 - distance).label("score"))
            .where(KnowledgeChunk.visibility == "public")
            .where(KnowledgeChunk.embedding_model == embedding_model)
            .order_by(distance)
            .limit(limit)
        )
        if project_id is not None:
            stmt = stmt.where(KnowledgeChunk.project_id == project_id)
        if document_types:
            stmt = stmt.where(KnowledgeChunk.document_type.in_(list(document_types)))
        rows = self.session.execute(stmt).all()
        return [
            ScoredChunk(
                document_id=c.document_id, document_title=c.document_title, document_type=c.document_type,
                project_id=c.project_id, section=c.section, chunk_index=c.chunk_index, content=c.content,
                content_hash=c.content_hash, url=c.url, score=float(score),
            )
            for c, score in rows
        ]

    def count_chunks(self, embedding_model: str | None = None) -> int:
        stmt = select(func.count()).select_from(KnowledgeChunk)
        if embedding_model:
            stmt = stmt.where(KnowledgeChunk.embedding_model == embedding_model)
        return int(self.session.execute(stmt).scalar_one())

    # ---- ingestion -------------------------------------------------------------------------
    def existing_chunks(self) -> list[KnowledgeChunk]:
        return list(self.session.execute(select(KnowledgeChunk)).scalars())

    def upsert_chunk(self, values: dict) -> None:
        stmt = insert(KnowledgeChunk).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values if k not in ("document_id", "chunk_index")}
        update_cols["updated_at"] = func.now()
        self.session.execute(stmt.on_conflict_do_update(constraint="uq_chunk_document_index", set_=update_cols))

    def delete_stale(self, document_id: str, keep_indexes: Sequence[int]) -> int:
        stmt = delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        if keep_indexes:
            stmt = stmt.where(KnowledgeChunk.chunk_index.not_in(list(keep_indexes)))
        return self.session.execute(stmt).rowcount or 0  # type: ignore[attr-defined]

    def delete_documents_not_in(self, document_ids: Sequence[str]) -> int:
        stmt = delete(KnowledgeChunk).where(KnowledgeChunk.document_id.not_in(list(document_ids)))
        return self.session.execute(stmt).rowcount or 0  # type: ignore[attr-defined]

    def start_run(self, embedding_model: str) -> int:
        run = IngestionRun(status="running", embedding_model=embedding_model)
        self.session.add(run)
        self.session.commit()
        return run.id

    def finish_run(self, run_id: int, status: str, stats: dict | None, error: str | None) -> None:
        run = self.session.get(IngestionRun, run_id)
        if run:
            run.status, run.stats, run.error, run.finished_at = status, stats, error, func.now()
            self.session.commit()


class RateLimitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def hit(self, key: str, window_start: int) -> int:
        """Atomically increment and return the counter for this key and window."""
        base = insert(RateLimitCounter).values(key=key, window_start=window_start, count=1)
        stmt = base.on_conflict_do_update(
            index_elements=["key", "window_start"], set_={"count": RateLimitCounter.count + 1}
        ).returning(RateLimitCounter.count)
        count = self.session.execute(stmt).scalar_one()
        self.session.commit()
        return int(count)

    def purge_before(self, window_start: int) -> None:
        self.session.execute(delete(RateLimitCounter).where(RateLimitCounter.window_start < window_start))
        self.session.commit()


def vector_column_dimensions(session: Session) -> int | None:
    """Dimension of the embedding column as the database sees it (pgvector stores it in atttypmod)."""
    row = session.execute(text(
        "SELECT atttypmod FROM pg_attribute "
        "WHERE attrelid = to_regclass('knowledge_chunks') AND attname = 'embedding'"
    )).first()
    return int(row[0]) if row and row[0] and row[0] > 0 else None

