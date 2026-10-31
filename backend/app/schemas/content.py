"""Typed models for the canonical knowledge files (profile.json and projects/*.json)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Contact(_Model):
    email: str
    phone: str | None = None
    show_phone: bool = False
    location: str | None = None
    show_location: bool = True
    linkedin: str | None = None
    github: str | None = None
    resume_url: str | None = None
    note: str | None = None
    # JSON uses "_note"; kept out of the public models.


class CareerJourneyItem(_Model):
    period: str
    label: str
    detail: str


class CareerInterests(_Model):
    roles: list[str]
    note: str


class Responsibility(_Model):
    verb: str
    text: str
    projects: list[str]


class Experience(_Model):
    id: str
    employer: str
    title: str
    start: str
    end: str
    dates: str
    location: str
    summary: str
    responsibilities: list[Responsibility]
    technologies: list[str]
    related_projects: list[str]
    related_projects_note: str | None = None


class Education(_Model):
    degree: str
    short: str
    institution: str
    start: str
    end: str
    dates: str
    location: str


class Course(_Model):
    title: str
    provider: str
    dates: str
    kind: str
    coverage: list[str]


SkillLevel = Literal["professional", "projects", "familiar", "exploring"]


class Skill(_Model):
    name: str
    level: SkillLevel
    evidence: str


class SkillCategory(_Model):
    category: str
    items: list[Skill]


class Profile(_Model):
    comment: str | None = None
    name: str
    display_name: str
    title: str
    headline: str
    tagline: str
    summary: str
    contact: Contact
    proof_points: list[str]
    biography: list[str]
    career_journey: list[CareerJourneyItem]
    current_focus: str
    engineering_interests: list[str]
    career_interests: CareerInterests
    experience: list[Experience]
    education: list[Education]
    courses: list[Course]
    skill_levels: dict[str, str]
    skills: list[SkillCategory]


Status = Literal["documented", "general", "unspecified"]


class Fact(_Model):
    label: str
    detail: str
    status: Status


class Step(_Model):
    step: str
    status: Status


class Contribution(_Model):
    type: str
    items: list[str]


class Project(_Model):
    id: str
    title: str
    category: str
    filters: list[str]
    featured: bool
    employer: str | None
    confidential: bool
    aliases: list[str]
    summary: str
    technologies: list[str]
    overview: str
    problem: str
    approach: list[str]
    architecture: list[Fact]
    workflow: list[Step]
    contribution: Contribution
    limitations: list[str]
    future_improvements: list[str]
    related_skills: list[str]
    related_projects: list[str]
    links: list[dict[str, str]]
