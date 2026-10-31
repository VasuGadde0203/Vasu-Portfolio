from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
        # No server-side prepared statements, so a pooled connection string (Neon's -pooler host,
        # PgBouncer in transaction mode) works as well as a direct one.
        connect_args={"prepare_threshold": None},
    )


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with _session_factory()() as session:
        yield session


def open_session() -> Session:
    """For scripts and the ingestion CLI."""
    return _session_factory()()
