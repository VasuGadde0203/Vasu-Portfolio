"""Alembic environment. Needs only DATABASE_URL (not the OpenAI settings)."""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.db.models import Base
from app.db.url import normalize_database_url

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def _url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:  # allow a local .env file
            from dotenv import dotenv_values  # type: ignore[import-not-found]
            url = dotenv_values(".env").get("DATABASE_URL")
        except ImportError:
            url = None
    if not url:
        sys.exit("DATABASE_URL is not set. See backend/.env.example.")
    return normalize_database_url(url)


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
