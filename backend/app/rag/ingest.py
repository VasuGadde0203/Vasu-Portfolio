"""Knowledge ingestion CLI:  python -m app.rag.ingest [--dry-run] [--force-reembed] [--no-prune]

Idempotent: unchanged chunks keep their embeddings and are not re-embedded. All database writes
for a run happen in one transaction, so a failed embedding call leaves the previous index intact.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings, load_settings_or_exit
from app.core.logging import configure_logging
from app.db.repositories import KnowledgeRepository, vector_column_dimensions
from app.db.session import open_session
from app.rag.chunking import Chunk, chunk_document
from app.rag.documents import load_documents
from app.services.errors import ServiceError
from app.services.openai_service import AIClient, OpenAIService

log = logging.getLogger("ingest")


@dataclass
class IngestStats:
    documents: int = 0
    chunks_total: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    embeddings_generated: int = 0


def build_chunks(settings: Settings) -> tuple[list[str], list[Chunk]]:
    docs = load_documents(settings.knowledge_dir)
    chunks = [c for d in docs for c in chunk_document(d, settings.chunk_max_chars, settings.chunk_overlap_chars)]
    return [d.document_id for d in docs], chunks


def ingest(
    session: Session,
    settings: Settings,
    ai: AIClient,
    *,
    force_reembed: bool = False,
    prune: bool = True,
    dry_run: bool = False,
) -> IngestStats:
    model = settings.openai_embedding_model
    db_dims = vector_column_dimensions(session)
    if db_dims is not None and db_dims != settings.embedding_dimensions:
        raise ServiceError("dimension_mismatch", f"Database vector column is {db_dims}-dimensional but "
                           f"EMBEDDING_DIMENSIONS={settings.embedding_dimensions}.", 500)

    repo = KnowledgeRepository(session)
    document_ids, chunks = build_chunks(settings)
    existing = {(c.document_id, c.chunk_index): c for c in repo.existing_chunks()}
    # Embeddings reusable by content hash, but only if produced by the current model.
    reusable: dict[str, list[float]] = {
        c.content_hash: list(c.embedding) for c in existing.values() if c.embedding_model == model
    }

    stats = IngestStats(documents=len(document_ids), chunks_total=len(chunks))
    to_embed: list[str] = []
    for ch in chunks:
        if (force_reembed or ch.content_hash not in reusable) and ch.content_hash not in to_embed:
            to_embed.append(ch.content_hash)
    text_by_hash = {c.content_hash: c.content for c in chunks}

    new_vectors: dict[str, list[float]] = {}
    if to_embed and not dry_run:
        vectors = ai.embed([text_by_hash[h] for h in to_embed])
        new_vectors = dict(zip(to_embed, vectors, strict=True))
        stats.embeddings_generated = len(vectors)
    elif dry_run:
        stats.embeddings_generated = len(to_embed)

    if dry_run:
        return stats

    try:
        by_doc: dict[str, list[int]] = {}
        for ch in chunks:
            vector = new_vectors.get(ch.content_hash) or reusable[ch.content_hash]
            prior = existing.get((ch.document_id, ch.chunk_index))
            if prior is None:
                stats.inserted += 1
            elif prior.content_hash == ch.content_hash and prior.embedding_model == model and not force_reembed:
                stats.unchanged += 1
                if _metadata_unchanged(prior, ch):
                    by_doc.setdefault(ch.document_id, []).append(ch.chunk_index)
                    continue
            else:
                stats.updated += 1
            repo.upsert_chunk({**{k: v for k, v in asdict(ch).items()}, "embedding": vector, "embedding_model": model})
            by_doc.setdefault(ch.document_id, []).append(ch.chunk_index)
        for doc_id, keep in by_doc.items():
            stats.deleted += repo.delete_stale(doc_id, keep)
        if prune:
            stats.deleted += repo.delete_documents_not_in(document_ids)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return stats


def _metadata_unchanged(prior, ch: Chunk) -> bool:  # noqa: ANN001
    return (prior.document_title, prior.document_type, prior.project_id, prior.section, prior.source_file,
            prior.url, prior.visibility) == (ch.document_title, ch.document_type, ch.project_id, ch.section,
                                             ch.source_file, ch.url, ch.visibility)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest the portfolio knowledge base into pgvector.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change; no API calls or writes.")
    parser.add_argument("--force-reembed", action="store_true", help="Re-embed every chunk (e.g. after a model change).")
    parser.add_argument("--no-prune", action="store_true", help="Keep chunks of documents no longer in the source.")
    args = parser.parse_args(argv)

    configure_logging()
    settings = load_settings_or_exit()
    session = open_session()
    repo = KnowledgeRepository(session)
    run_id = None if args.dry_run else repo.start_run(settings.openai_embedding_model)
    try:
        stats = ingest(session, settings, OpenAIService(settings), force_reembed=args.force_reembed,
                       prune=not args.no_prune, dry_run=args.dry_run)
    except ServiceError as exc:
        _finish(repo, run_id, "failed", None, f"{exc.code}: {exc.message}")
        log.error("Ingestion failed: %s (%s)", exc.message, exc.code)
        return 1
    except Exception as exc:  # noqa: BLE001 - recorded, then reported without a stack trace to stdout
        _finish(repo, run_id, "failed", None, f"{type(exc).__name__}: {exc}"[:2000])
        log.exception("Ingestion failed")
        return 1
    _finish(repo, run_id, "succeeded", asdict(stats), None)
    print(json.dumps({"dry_run": args.dry_run, **asdict(stats)}, indent=2))
    return 0


def _finish(repo: KnowledgeRepository, run_id: int | None, status: str, stats: dict | None, error: str | None) -> None:
    if run_id is None:
        return
    repo.session.rollback()
    repo.finish_run(run_id, status, stats, error)


if __name__ == "__main__":
    raise SystemExit(run())
