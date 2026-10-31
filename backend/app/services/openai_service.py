"""The only module that talks to OpenAI. Runs server-side; the key never reaches the browser."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Protocol

import openai
from openai import OpenAI

from app.core.config import Settings
from app.services.errors import ServiceError

log = logging.getLogger(__name__)


class AIClient(Protocol):
    embedding_model: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

    def complete(self, messages: list[dict[str, str]]) -> str: ...


def translate_openai_error(exc: Exception) -> ServiceError:
    """Map SDK exceptions to safe, generic messages. Never include the raw error text."""
    if isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError):
        log.error("OpenAI rejected the configured credentials")
        return ServiceError("ai_unavailable", "The assistant is temporarily unavailable.", 503)
    if isinstance(exc, openai.RateLimitError):
        return ServiceError("ai_busy", "The assistant is busy right now. Please try again shortly.", 429)
    if isinstance(exc, openai.APITimeoutError):
        return ServiceError("ai_timeout", "The assistant took too long to respond. Please try again.", 504)
    if isinstance(exc, openai.APIConnectionError):
        return ServiceError("ai_unavailable", "The assistant is temporarily unavailable.", 503)
    if isinstance(exc, openai.BadRequestError):
        log.error("OpenAI rejected the request (status %s)", exc.status_code)
        return ServiceError("ai_request_rejected", "That question could not be processed. Try rephrasing it.", 400)
    if isinstance(exc, openai.APIStatusError):
        log.error("OpenAI returned status %s", exc.status_code)
        return ServiceError("ai_unavailable", "The assistant is temporarily unavailable.", 503)
    log.exception("Unexpected error calling OpenAI")
    return ServiceError("ai_error", "Something went wrong while generating a response.", 502)


class OpenAIService:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self._settings = settings
        self.embedding_model = settings.openai_embedding_model
        # Bounded retries (SDK backs off exponentially) and a hard timeout cap cost and latency.
        self._client = client or OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout,
            max_retries=settings.openai_max_retries,
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        dims = self._settings.embedding_dimensions
        vectors: list[list[float]] = []
        batch = self._settings.openai_embedding_batch_size
        for start in range(0, len(texts), batch):
            part = list(texts[start:start + batch])
            kwargs: dict = {"model": self.embedding_model, "input": part}
            if self.embedding_model.startswith("text-embedding-3"):
                kwargs["dimensions"] = dims
            try:
                resp = self._client.embeddings.create(**kwargs)
            except openai.OpenAIError as exc:
                raise translate_openai_error(exc) from exc
            data = sorted(resp.data, key=lambda d: d.index)
            if len(data) != len(part):
                raise ServiceError("embedding_mismatch", "Embedding service returned an unexpected result.", 502)
            vectors.extend(d.embedding for d in data)
        validate_dimensions(vectors, dims)
        return vectors

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._settings.openai_chat_model,
                messages=messages,  # type: ignore[arg-type]
                max_completion_tokens=self._settings.openai_max_output_tokens,
            )
        except openai.OpenAIError as exc:
            raise translate_openai_error(exc) from exc
        choice = resp.choices[0] if resp.choices else None
        text = (choice.message.content or "").strip() if choice else ""
        if not text:
            reason = choice.finish_reason if choice else "no_choices"
            log.warning("Empty completion (finish_reason=%s)", reason)
            raise ServiceError("empty_response", "The assistant did not produce an answer. Please try again.", 502)
        return text


def validate_dimensions(vectors: Sequence[Sequence[float]], expected: int) -> None:
    for v in vectors:
        if len(v) != expected:
            raise ServiceError(
                "embedding_dimension_mismatch",
                f"Embedding has {len(v)} dimensions but {expected} are configured.", 500)
