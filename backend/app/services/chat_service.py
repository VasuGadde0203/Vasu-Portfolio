"""Orchestrates one chat turn: resolve context -> embed -> retrieve -> generate -> cite."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.repositories import KnowledgeRepository
from app.rag.citations import (
    build_sources,
    opens_with_decline,
    project_links,
    remove_unverified_links,
    strip_markers,
)
from app.rag.prompts import NO_EVIDENCE_ANSWER, build_messages
from app.rag.query import HintDetector, normalize_query, resolve_query
from app.rag.retrieval import retrieve
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.errors import ServiceError
from app.services.openai_service import AIClient

log = logging.getLogger(__name__)


class ChatService:
    def __init__(self, settings: Settings, ai: AIClient, hints: HintDetector) -> None:
        self._s = settings
        self._ai = ai
        self._hints = hints

    def answer(self, session: Session, request: ChatRequest) -> ChatResponse:
        message = normalize_query(request.message)
        history = request.history[-self._s.max_history_messages:] if self._s.max_history_messages else []

        retrieval_query = resolve_query(message, history)
        hints = self._hints.detect(message, history)
        embedding = self._ai.embed([retrieval_query])[0]  # the only embedding call per question

        try:
            result = retrieve(KnowledgeRepository(session), embedding, hints, self._s, self._ai.embedding_model)
        except SQLAlchemyError as exc:
            log.error("Retrieval query failed (%s)", type(exc).__name__)
            raise ServiceError("knowledge_unavailable", "The knowledge base is temporarily unavailable.", 503) from exc

        if not result.chunks:  # nothing relevant: do not spend a chat completion on it
            return ChatResponse(answer=NO_EVIDENCE_ANSWER, sources=[], project_ids=[], evidence="none")

        raw = self._ai.complete(build_messages(message, history, result.chunks))
        sources = build_sources(raw, result.chunks)
        project_ids = list(dict.fromkeys(s.project_id for s in sources if s.project_id))
        contact = self._hints.profile.contact
        allowed = {u for u in (contact.linkedin, contact.github) if u}
        answer = remove_unverified_links(strip_markers(raw), allowed)
        if not opens_with_decline(answer):  # no "learn more" links under an answer that declined the question
            answer += project_links(project_ids, self._hints.projects)
        return ChatResponse(answer=answer, sources=sources, project_ids=project_ids, evidence=result.evidence)
