from __future__ import annotations

import hashlib
import math
import os
import re
from collections.abc import Sequence

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql://portfolio:devpass@localhost:5433/portfolio_test")

# Settings must be resolvable at import time of the app modules.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")
os.environ.setdefault("OPENAI_CHAT_MODEL", "test-chat-model")
os.environ.setdefault("OPENAI_EMBEDDING_MODEL", "test-embedding-model")
os.environ["DATABASE_URL"] = TEST_DB
os.environ["ENVIRONMENT"] = "test"

from app.core.config import Settings, get_settings  # noqa: E402

_STOP = {"the", "a", "an", "of", "to", "and", "in", "is", "are", "what", "did", "does", "do", "his", "he", "for",
         "with", "on", "at", "how", "was", "were", "me", "about", "tell", "vasu", "s", "it", "that", "this"}


def fake_embedding(text: str, dims: int = 1536) -> list[float]:
    """Deterministic lexical embedding (hashed bag of words). Tests plumbing, NOT semantic quality."""
    vec = [0.0] * dims
    for tok in re.findall(r"[a-z0-9\.\+]+", text.lower()):
        tok = tok.rstrip("s") if len(tok) > 3 else tok
        if tok in _STOP:
            continue
        vec[int(hashlib.md5(tok.encode()).hexdigest(), 16) % dims] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeAI:
    def __init__(self, embedding_model: str = "fake-embed-v1", answer: str = "Documented answer. [1]") -> None:
        self.embedding_model = embedding_model
        self.answer = answer
        self.embed_calls: list[list[str]] = []
        self.complete_calls: list[list[dict[str, str]]] = []
        self.error: Exception | None = None

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.error:
            raise self.error
        self.embed_calls.append(list(texts))
        return [fake_embedding(t) for t in texts]

    def complete(self, messages: list[dict[str, str]]) -> str:
        if self.error:
            raise self.error
        self.complete_calls.append(messages)
        return self.answer

    @property
    def embedded_total(self) -> int:
        return sum(len(c) for c in self.embed_calls)


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return get_settings().model_copy(update={"retrieval_min_score": 0.05, "retrieval_strong_score": 0.2})


@pytest.fixture
def fake_ai() -> FakeAI:
    return FakeAI()
