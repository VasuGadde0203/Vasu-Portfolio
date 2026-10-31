"""Database URL helpers shared by the app and Alembic (which must not need OpenAI settings)."""

from __future__ import annotations


def normalize_database_url(url: str) -> str:
    """Hosted providers (e.g. Railway) hand out `postgresql://` or `postgres://`; use psycopg 3."""
    url = url.strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url
