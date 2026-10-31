from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def _limit(cls, v: str) -> str:
        if len(v) > get_settings().max_history_message_chars:
            raise ValueError("History message too long")
        return v


class ChatRequest(BaseModel):
    """History is held in the visitor's browser and replayed here; it is context, not fact."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    history: list[ChatTurn] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def _message(cls, v: str) -> str:
        v = v.strip()
        s = get_settings()
        if not v:
            raise ValueError("Message must not be empty")
        if len(v) > s.max_message_chars:
            raise ValueError(f"Message must be at most {s.max_message_chars} characters")
        return v

    @field_validator("history")
    @classmethod
    def _history(cls, v: list[ChatTurn]) -> list[ChatTurn]:
        limit = get_settings().max_history_messages
        if len(v) > limit:
            raise ValueError(f"History must contain at most {limit} messages")
        return v


class Source(BaseModel):
    document_id: str
    title: str
    section: str | None = None
    project_id: str | None = None
    url: str | None = None


Evidence = Literal["strong", "partial", "none"]


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    project_ids: list[str]
    # Heuristic based on retrieval similarity; it is not a measure of factual accuracy.
    evidence: Evidence


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
