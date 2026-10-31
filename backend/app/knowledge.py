"""Loads and validates the canonical knowledge files. This is the single source of truth."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.content import Profile, Project


class KnowledgeError(RuntimeError):
    pass


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"Cannot read knowledge file {path}: {exc}") from exc


def load_profile(knowledge_dir: Path | None = None) -> Profile:
    root = knowledge_dir or get_settings().knowledge_dir
    raw = _read_json(root / "profile.json")
    raw["comment"] = raw.pop("_comment", None)
    contact = raw["contact"]
    contact["note"] = contact.pop("_note", None)
    return Profile.model_validate(raw)


def load_projects(knowledge_dir: Path | None = None) -> list[Project]:
    root = knowledge_dir or get_settings().knowledge_dir
    projects = [Project.model_validate(_read_json(p)) for p in sorted((root / "projects").glob("*.json"))]
    ids = {p.id for p in projects}
    for project in projects:
        missing = [r for r in project.related_projects if r not in ids]
        if missing:
            raise KnowledgeError(f"Project {project.id} references unknown projects: {missing}")
    return projects


def public_profile(profile: Profile) -> Profile:
    """Strip private fields. The phone number is only published when explicitly enabled."""
    contact = profile.contact.model_copy()
    if not contact.show_phone:
        contact.phone = None
    if not contact.show_location:
        contact.location = None
    return profile.model_copy(update={"contact": contact, "comment": None})
