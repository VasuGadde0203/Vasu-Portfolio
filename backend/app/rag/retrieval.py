"""Semantic retrieval with metadata boosting, thresholding, de-duplication and a bounded context."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.db.repositories import KnowledgeRepository, ScoredChunk
from app.rag.query import Hints
from app.schemas.chat import Evidence


@dataclass(frozen=True)
class Retrieved:
    chunks: list[ScoredChunk]
    evidence: Evidence
    project_id: str | None


def rank_and_select(
    candidates: list[ScoredChunk], hints: Hints, s: Settings
) -> list[ScoredChunk]:
    """Pure function (unit-tested): threshold, boost, de-duplicate, cap, bound context size."""
    scored: list[tuple[float, ScoredChunk]] = []
    for c in candidates:
        if c.score < s.retrieval_min_score:
            continue
        boost = s.retrieval_project_boost if hints.project_id and c.project_id == hints.project_id else 0.0
        scored.append((c.score + boost, c))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    selected: list[ScoredChunk] = []
    seen_keys: set[tuple[str, int]] = set()
    seen_hashes: set[str] = set()
    per_doc: dict[str, int] = {}
    budget = s.max_context_chars
    for _, c in scored:
        key = (c.document_id, c.chunk_index)
        if key in seen_keys or c.content_hash in seen_hashes:
            continue
        if per_doc.get(c.document_id, 0) >= s.retrieval_max_chunks_per_document:
            continue
        if len(selected) >= s.retrieval_top_k:
            break
        if selected and len(c.content) > budget:
            continue  # keep at least one chunk, then respect the character budget
        seen_keys.add(key)
        seen_hashes.add(c.content_hash)
        per_doc[c.document_id] = per_doc.get(c.document_id, 0) + 1
        budget -= len(c.content)
        selected.append(c)
    return selected


def assess_evidence(chunks: list[ScoredChunk], s: Settings) -> Evidence:
    if not chunks:
        return "none"
    top = max(c.score for c in chunks)
    return "strong" if top >= s.retrieval_strong_score else "partial"


def retrieve(
    repo: KnowledgeRepository, embedding: list[float], hints: Hints, s: Settings, embedding_model: str
) -> Retrieved:
    candidates = repo.search(embedding, embedding_model=embedding_model, limit=s.retrieval_candidates)
    if hints.project_id:  # make sure the asked-about project's own documents are considered
        candidates += repo.search(embedding, embedding_model=embedding_model, limit=5, project_id=hints.project_id)
    if hints.technologies:  # technology questions should also surface the skills evidence
        candidates += repo.search(embedding, embedding_model=embedding_model, limit=2, document_types=["skills"])
    selected = rank_and_select(candidates, hints, s)
    return Retrieved(chunks=selected, evidence=assess_evidence(selected, s), project_id=hints.project_id)
