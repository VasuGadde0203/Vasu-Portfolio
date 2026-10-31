"""Centralised, validated configuration. All settings come from environment variables."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.url import normalize_database_url

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: Literal["development", "test", "production"] = "development"

    # OpenAI (server-side only; never exposed to the browser)
    openai_api_key: SecretStr = Field(min_length=1)
    openai_chat_model: str = Field(min_length=1)
    openai_embedding_model: str = Field(min_length=1)
    openai_timeout: float = Field(default=30.0, gt=0, le=120)
    openai_max_output_tokens: int = Field(default=600, ge=50, le=4000)
    openai_embedding_batch_size: int = Field(default=64, ge=1, le=512)
    openai_max_retries: int = Field(default=2, ge=0, le=5)
    # Must equal the pgvector column dimension (see app.db.models.VECTOR_DIMENSIONS).
    embedding_dimensions: int = Field(default=1536, ge=8, le=4096)

    # Database
    database_url: str = Field(min_length=1)

    # HTTP
    allowed_origins: str = "http://localhost:5173"
    trust_proxy_headers: bool = False
    max_request_body_bytes: int = Field(default=32_768, ge=1024)

    # Abuse and cost controls
    rate_limit_per_minute: int = Field(default=10, ge=1)
    rate_limit_per_day: int = Field(default=150, ge=1)
    max_message_chars: int = Field(default=600, ge=20, le=4000)
    max_history_messages: int = Field(default=6, ge=0, le=20)
    max_history_message_chars: int = Field(default=1500, ge=50, le=8000)

    # Contact form (messages are stored in the same PostgreSQL database)
    contact_rate_limit_per_hour: int = Field(default=5, ge=1)

    # Retrieval
    retrieval_top_k: int = Field(default=6, ge=1, le=20)
    retrieval_candidates: int = Field(default=18, ge=1, le=100)
    retrieval_min_score: float = Field(default=0.30, ge=0.0, le=1.0)
    retrieval_strong_score: float = Field(default=0.45, ge=0.0, le=1.0)
    retrieval_project_boost: float = Field(default=0.05, ge=0.0, le=0.5)
    retrieval_max_chunks_per_document: int = Field(default=3, ge=1, le=10)
    max_context_chars: int = Field(default=6000, ge=500, le=30000)

    # Chunking
    chunk_max_chars: int = Field(default=1100, ge=200, le=4000)
    chunk_overlap_chars: int = Field(default=120, ge=0, le=1000)

    # Knowledge base
    knowledge_dir: Path = BACKEND_DIR / "knowledge"

    @field_validator("database_url")
    @classmethod
    def _normalise_db_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @model_validator(mode="after")
    def _cross_checks(self) -> Settings:
        from app.db.models import VECTOR_DIMENSIONS

        if self.embedding_dimensions != VECTOR_DIMENSIONS:
            raise ValueError(
                f"EMBEDDING_DIMENSIONS={self.embedding_dimensions} does not match the database "
                f"vector column ({VECTOR_DIMENSIONS}). Changing dimensions requires a new Alembic "
                "migration and a full re-embed; see docs/DEPLOYMENT.md."
            )
        if self.chunk_overlap_chars >= self.chunk_max_chars:
            raise ValueError("CHUNK_OVERLAP_CHARS must be smaller than CHUNK_MAX_CHARS.")
        if self.retrieval_strong_score < self.retrieval_min_score:
            raise ValueError("RETRIEVAL_STRONG_SCORE must be >= RETRIEVAL_MIN_SCORE.")
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError("ALLOWED_ORIGINS must list explicit origins in production, not '*'.")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.allowed_origins.split(",") if o.strip()]


def format_validation_error(exc: ValidationError) -> str:
    lines = ["Invalid or missing configuration:"]
    for err in exc.errors():
        name = ".".join(str(p) for p in err["loc"]).upper() or "SETTINGS"
        lines.append(f"  - {name}: {err['msg']}")
    lines.append("See backend/.env.example for the required environment variables.")
    return "\n".join(lines)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required values come from the environment


def load_settings_or_exit() -> Settings:
    """Used by entry points (server startup, CLI) to fail fast with a helpful message."""
    try:
        return get_settings()
    except ValidationError as exc:
        print(format_validation_error(exc), file=sys.stderr)
        raise SystemExit(1) from None
