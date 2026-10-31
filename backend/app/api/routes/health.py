from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.repositories import KnowledgeRepository, vector_column_dimensions
from app.db.session import get_session

log = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class Liveness(BaseModel):
    status: str


class Readiness(BaseModel):
    status: str
    database: bool
    pgvector: bool
    schema_ready: bool
    embedding_dimensions_match: bool
    knowledge_indexed: bool


@router.get("/health", response_model=Liveness)
def health() -> Liveness:
    """Liveness only: the process is up. Use /health/ready for dependencies."""
    return Liveness(status="ok")


@router.get("/health/ready", response_model=Readiness)
def ready(response: Response, session: Session = Depends(get_session),
          settings: Settings = Depends(get_settings)) -> Readiness:
    r = Readiness(status="not_ready", database=False, pgvector=False, schema_ready=False,
                  embedding_dimensions_match=False, knowledge_indexed=False)
    try:
        session.execute(text("SELECT 1"))
        r.database = True
        r.pgvector = session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first() is not None
        dims = vector_column_dimensions(session)
        r.schema_ready = dims is not None
        r.embedding_dimensions_match = dims == settings.embedding_dimensions
        if r.schema_ready:
            r.knowledge_indexed = KnowledgeRepository(session).count_chunks(settings.openai_embedding_model) > 0
    except Exception as exc:  # noqa: BLE001 - details intentionally not exposed in the response
        session.rollback()
        # Server log only (never returned to the caller): the error type and the first line of the database's
        # message, which names the problem (e.g. authentication failed, unknown host) but never the password.
        log.error("Readiness check failed (%s): %s", type(exc).__name__, str(exc).splitlines()[0][:200] if str(exc) else "")
    ok = r.database and r.pgvector and r.schema_ready and r.embedding_dimensions_match and r.knowledge_indexed
    r.status = "ready" if ok else "not_ready"
    if not ok:
        response.status_code = 503
    return r
