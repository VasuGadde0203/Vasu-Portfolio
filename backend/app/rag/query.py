"""Query normalisation, follow-up resolution and project/technology hints. No LLM call needed."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.schemas.chat import ChatTurn
from app.schemas.content import Profile, Project

_FOLLOW_UP_TOKENS = re.compile(
    r"\b(he|his|him|she|her|it|its|that|this|those|these|they|them|their|there|the project|the system|"
    r"the pipeline|same|also|more|what about|how about|and)\b", re.IGNORECASE)


def normalize_query(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


def is_follow_up(message: str) -> bool:
    return len(message.split()) <= 8 or bool(_FOLLOW_UP_TOKENS.search(message))


def resolve_query(message: str, history: list[ChatTurn]) -> str:
    """Prepend the previous visitor question when the new one reads like a follow-up.

    Assistant turns are deliberately not used for retrieval: they are unverified context."""
    previous = next((t.content for t in reversed(history) if t.role == "user"), None)
    if previous and is_follow_up(message):
        return f"{normalize_query(previous)} {message}"[:1200]
    return message


@dataclass(frozen=True)
class Hints:
    project_id: str | None
    technologies: list[str]


class HintDetector:
    def __init__(self, projects: list[Project], profile: Profile) -> None:
        self.projects = {p.id: p for p in projects}
        self.profile = profile
        self._aliases: dict[str, list[str]] = {}
        for p in projects:
            names = {p.id.replace("-", " "), p.title.lower(), *[a.lower() for a in p.aliases]}
            self._aliases[p.id] = sorted(names, key=len, reverse=True)
        self._technologies = sorted(
            {s.name for cat in profile.skills for s in cat.items}
            | {t for p in projects for t in p.technologies}, key=len, reverse=True)

    @staticmethod
    def _contains(text: str, phrase: str) -> bool:
        return re.search(rf"(?<![\w]){re.escape(phrase.lower())}(?![\w])", text.lower()) is not None

    def project_in(self, text: str) -> str | None:
        best: tuple[int, str] | None = None
        for pid, names in self._aliases.items():
            score = sum(len(n) for n in names if self._contains(text, n))
            if score and (best is None or score > best[0]):
                best = (score, pid)
        return best[1] if best else None

    def detect(self, message: str, history: list[ChatTurn]) -> Hints:
        project = self.project_in(message)
        if project is None and is_follow_up(message):
            for turn in reversed(history):
                project = self.project_in(turn.content)
                if project:
                    break
        techs = [t for t in self._technologies if self._contains(message, t)]
        return Hints(project_id=project, technologies=techs[:5])
