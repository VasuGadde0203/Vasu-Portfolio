"""Citation handling: only chunks that were actually retrieved can ever be cited."""

from __future__ import annotations

import re

from app.db.repositories import ScoredChunk
from app.schemas.chat import Source
from app.schemas.content import Project

_MARKER = re.compile(r"\s?\[(\d{1,2})\]")
_ABSTAIN = re.compile(r"\b(i don't have|i do not have|not documented|no verified|isn't documented|cannot find)\b",
                      re.IGNORECASE)


def extract_cited_indexes(answer: str, n_chunks: int) -> list[int]:
    seen: list[int] = []
    for m in _MARKER.finditer(answer):
        idx = int(m.group(1))
        if 1 <= idx <= n_chunks and idx not in seen:
            seen.append(idx)
    return seen


def opens_with_decline(answer: str) -> bool:
    """True when the answer starts by saying it has no verified information on the question."""
    return _ABSTAIN.search(answer[:120]) is not None


def strip_markers(answer: str) -> str:
    return _MARKER.sub("", answer).strip()


_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
_BARE_URL = re.compile(r"https?://[^\s)>\]]+")
_BARE_SITE_PATH = re.compile(r"(?<![\w/:.#-])/(?:projects/[a-z0-9-]+|skills|experience|about|contact|resume)\b")


def remove_unverified_links(answer: str, allowed: set[str]) -> str:
    """The model never gets to invent a link. Markdown links, bare URLs and bare site paths survive
    only if they are in `allowed` (URLs that came from the knowledge base); otherwise the label stays
    and the target goes. Verified links are appended separately by `project_links`."""
    text = _MD_LINK.sub(lambda m: m.group(1), answer)
    text = _BARE_URL.sub(lambda m: m.group(0) if m.group(0).rstrip(".,;") in allowed else "", text)
    text = _BARE_SITE_PATH.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", re.sub(r"\s+([.,;])", r"\1", text)).strip()


def project_links(project_ids: list[str], projects: dict[str, Project], limit: int = 3) -> str:
    """Markdown list of case-study (and GitHub) links, built only from known project records."""
    rows = []
    for pid in project_ids:
        p = projects.get(pid)
        if p is None:
            continue
        parts = [f"[{p.title} case study](/projects/{p.id})"]
        parts += [f"[{link['label']}]({link['url']})" for link in p.links
                  if link.get("url", "").startswith("https://github.com/")]
        rows.append("- " + " · ".join(parts))
        if len(rows) == limit:
            break
    if not rows:
        return ""
    return ("\n\n**Learn more**\n" if len(rows) > 1 else "\n\n**Learn more:** ") + (
        "\n".join(rows) if len(rows) > 1 else rows[0][2:])


def to_source(c: ScoredChunk) -> Source:
    return Source(document_id=c.document_id, title=c.document_title, section=c.section,
                  project_id=c.project_id, url=c.url)


def build_sources(answer: str, chunks: list[ScoredChunk]) -> list[Source]:
    """Sources are the chunks the model cited. If it cited none and did not decline, fall back
    to the single top-ranked retrieved chunk rather than guessing."""
    cited = extract_cited_indexes(answer, len(chunks))
    if cited:
        picked = [chunks[i - 1] for i in cited]
    elif chunks and not _ABSTAIN.search(answer):
        picked = [chunks[0]]
    else:
        picked = []
    sources: list[Source] = []
    seen: set[tuple[str, str]] = set()
    for c in picked:
        key = (c.document_id, c.section)
        if key not in seen:
            seen.add(key)
            sources.append(to_source(c))
    return sources
