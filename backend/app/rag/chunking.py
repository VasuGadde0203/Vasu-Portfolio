"""Section-aware chunking. A section that fits stays whole; long ones split on paragraph/line
boundaries with a small overlap so context is not lost at chunk edges."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.rag.documents import Document


@dataclass(frozen=True)
class Chunk:
    document_id: str
    document_title: str
    document_type: str
    project_id: str | None
    section: str
    chunk_index: int
    content: str
    content_hash: str
    source_file: str
    url: str | None
    visibility: str


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    units: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        while len(line) > max_chars:  # a single very long line: cut at a space where possible
            cut = line.rfind(" ", 0, max_chars)
            cut = cut if cut > max_chars // 2 else max_chars
            units.append(line[:cut].strip())
            line = line[cut:].strip()
        if line:
            units.append(line)
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for unit in units:
        if current and size + len(unit) + 1 > max_chars:
            pieces.append("\n".join(current))
            tail = pieces[-1][-overlap:] if overlap else ""
            current = [tail.strip()] if tail.strip() else []
            size = len(current[0]) if current else 0
        current.append(unit)
        size += len(unit) + 1
    if current:
        pieces.append("\n".join(current))
    return pieces


def chunk_document(doc: Document, max_chars: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section in doc.sections:
        header = f"{doc.title} — {section.title}"
        for piece in split_text(section.text, max_chars, overlap):
            body = f"{header}\n{piece}"
            chunks.append(Chunk(
                document_id=doc.document_id, document_title=doc.title, document_type=doc.document_type,
                project_id=doc.project_id, section=section.title, chunk_index=len(chunks),
                content=body, content_hash=content_hash(body), source_file=doc.source_file,
                url=doc.url, visibility=doc.visibility,
            ))
    return chunks
