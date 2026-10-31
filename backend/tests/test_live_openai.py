"""Optional: exercises the real OpenAI API. Run with  TEST_LIVE_OPENAI=1 OPENAI_API_KEY=... pytest -m openai_live"""

import os

import pytest

pytestmark = pytest.mark.openai_live

if os.environ.get("TEST_LIVE_OPENAI") != "1":
    pytest.skip("set TEST_LIVE_OPENAI=1 (and real OPENAI_* variables) to run", allow_module_level=True)


def test_real_embedding_has_configured_dimensions():
    from app.core.config import Settings
    from app.services.openai_service import OpenAIService

    settings = Settings()  # type: ignore[call-arg]
    vectors = OpenAIService(settings).embed(["Applied AI engineer with RAG experience"])
    assert len(vectors) == 1 and len(vectors[0]) == settings.embedding_dimensions


def test_real_chat_completion_returns_text():
    from app.core.config import Settings
    from app.services.openai_service import OpenAIService

    reply = OpenAIService(Settings()).complete([{"role": "user", "content": "Reply with the single word: ok"}])  # type: ignore[call-arg]
    assert reply.strip()
