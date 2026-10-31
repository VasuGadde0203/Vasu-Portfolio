import pytest
from pydantic import ValidationError

from app.core.config import Settings, format_validation_error
from app.db.url import normalize_database_url

BASE = {"openai_api_key": "sk-x", "openai_chat_model": "m", "openai_embedding_model": "e",
        "database_url": "postgres://u:p@h:5432/d"}


def make(**over):
    return Settings(_env_file=None, **{**BASE, **over})


def test_database_url_is_normalised_for_psycopg3():
    assert normalize_database_url("postgres://u@h/d") == "postgresql+psycopg://u@h/d"
    assert normalize_database_url("postgresql://u@h/d") == "postgresql+psycopg://u@h/d"
    assert make().database_url.startswith("postgresql+psycopg://")


def test_missing_required_values_give_helpful_message(monkeypatch):
    for k in ("OPENAI_API_KEY", "OPENAI_CHAT_MODEL", "OPENAI_EMBEDDING_MODEL", "DATABASE_URL"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    message = format_validation_error(exc.value)
    assert "OPENAI_API_KEY" in message and "OPENAI_CHAT_MODEL" in message and ".env.example" in message


def test_embedding_dimension_must_match_database_column():
    with pytest.raises(ValidationError, match="does not match the database"):
        make(embedding_dimensions=3072)


def test_wildcard_origin_rejected_in_production():
    with pytest.raises(ValidationError, match="explicit origins"):
        make(environment="production", allowed_origins="*")
    assert make(allowed_origins="https://a.app/, https://b.app").cors_origins == ["https://a.app", "https://b.app"]


def test_overlap_must_be_smaller_than_chunk():
    with pytest.raises(ValidationError):
        make(chunk_max_chars=300, chunk_overlap_chars=300)


def test_api_key_is_not_in_repr():
    assert "sk-x" not in repr(make())
