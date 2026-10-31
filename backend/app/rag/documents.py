"""Turns the canonical knowledge files into sectioned, public documents ready for chunking."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from app.knowledge import load_profile, load_projects
from app.schemas.content import Profile, Project


@dataclass(frozen=True)
class Section:
    title: str
    text: str


@dataclass(frozen=True)
class Document:
    document_id: str  # deterministic and stable across runs
    title: str
    document_type: str
    source_file: str
    sections: list[Section]
    project_id: str | None = None
    url: str | None = None
    visibility: str = "public"
    metadata: dict[str, str] = field(default_factory=dict)


def _bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


def profile_documents(profile: Profile) -> list[Document]:
    src = "profile.json"
    docs: list[Document] = []
    c = profile.contact

    docs.append(Document(
        document_id="profile",
        title=f"{profile.display_name} — Profile",
        document_type="profile",
        source_file=src,
        url="/about",
        sections=[
            Section("Summary", f"{profile.name}. {profile.title}.\n{profile.summary}\n"
                    "The '2+ years' figure is the combined experience stated in the resume; "
                    "no more precise total is documented."),
            Section("Biography", "\n".join(profile.biography)),
            Section("Current Focus", profile.current_focus),
            Section("Engineering Interests", _bullets(profile.engineering_interests)),
            Section("Career Journey", _bullets(f"{j.period}: {j.label}. {j.detail}" for j in profile.career_journey)),
        ],
    ))

    contact_lines = [f"Email: {c.email}"]
    if c.show_location and c.location:
        contact_lines.append(f"Location: {c.location}")
    if c.linkedin:
        contact_lines.append(f"LinkedIn: {c.linkedin}")
    if c.github:
        contact_lines.append(f"GitHub: {c.github}")
    contact_lines.append("The best way to get in touch is by email or via the Contact page.")
    docs.append(Document(
        document_id="contact", title=f"How to contact {profile.display_name}", document_type="contact",
        source_file=src, url="/contact", sections=[Section("Contact", "\n".join(contact_lines))],
    ))

    docs.append(Document(
        document_id="career-interests", title="Career Interests", document_type="profile",
        source_file=src, url="/about",
        sections=[Section("Roles of Interest", _bullets(profile.career_interests.roles) + "\n" + profile.career_interests.note)],
    ))

    for exp in profile.experience:
        lines = [f"{exp.title} at {exp.employer}, {exp.dates}, {exp.location}.", exp.summary]
        resp = _bullets(r.text for r in exp.responsibilities)
        sections = [
            Section("Overview", "\n".join(lines)),
            Section("Documented Responsibilities and Contributions", resp),
            Section("Technologies", ", ".join(exp.technologies)),
        ]
        if exp.related_projects_note:
            sections.append(Section("Related Projects", exp.related_projects_note))
        docs.append(Document(
            document_id=f"experience-{exp.id}", title=f"{exp.employer} — {exp.title}",
            document_type="experience", source_file=src, url=f"/experience#{exp.id}", sections=sections,
        ))

    docs.append(Document(
        document_id="skills", title="Technical Skills", document_type="skills",
        source_file=src, url="/skills",
        sections=[
            Section(cat.category, "\n".join(
                f"- {s.name} ({profile.skill_levels[s.level]}): {s.evidence}" for s in cat.items))
            for cat in profile.skills
        ],
    ))

    docs.append(Document(
        document_id="education", title="Education", document_type="education",
        source_file=src, url="/about",
        sections=[Section(e.short, f"{e.degree}, {e.institution}, {e.dates}, {e.location}.") for e in profile.education],
    ))
    docs.append(Document(
        document_id="courses", title="Courses and Certifications", document_type="course",
        source_file=src, url="/about",
        sections=[Section(c.title, f"{c.title} from {c.provider}, {c.dates}. {c.kind}.\nCoverage: " + "; ".join(c.coverage))
                  for c in profile.courses],
    ))
    return docs


def project_document(p: Project) -> Document:
    def tagged(items: list[tuple[str, str]]) -> str:
        return "\n".join(f"- [{status}] {text}" for status, text in items)

    arch = tagged([(f.status, f"{f.label}: {f.detail}") for f in p.architecture])
    flow = tagged([(s.status, s.step) for s in p.workflow])
    employer = f"Employer context: {p.employer}." if p.employer else "Employer: not stated in the resume."
    sections = [
        Section("Overview", f"{p.title} ({p.category}). {p.overview}\n{employer}"),
        Section("Technologies", ", ".join(p.technologies)),
        Section("Problem Statement", p.problem),
        Section("Technical Approach", _bullets(p.approach)),
        Section("Architecture", "Status tags: documented = stated in the resume; general = general "
                "reasoning, not a verified detail; unspecified = not stated.\n" + arch),
        Section("Workflow", flow),
        Section("Documented Contribution", f"{p.contribution.type}.\n" + _bullets(p.contribution.items)),
        Section("Limitations", _bullets(p.limitations)),
        Section("Possible Future Improvements", "These are possible directions, not completed work.\n"
                + _bullets(p.future_improvements)),
    ]
    return Document(
        document_id=f"project-{p.id}", title=p.title, document_type="project",
        source_file=f"projects/{p.id}.json", project_id=p.id, url=f"/projects/{p.id}", sections=sections,
    )


_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def markdown_document(path: Path, root: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    h1 = _H1.search(text)
    title = h1.group(1) if h1 else path.stem.replace("_", " ").title()
    body = text[h1.end():] if h1 else text
    parts = _H2.split(body)
    sections: list[Section] = []
    preamble = parts[0].strip()
    if preamble:
        sections.append(Section("Introduction", preamble))
    for heading, content in zip(parts[1::2], parts[2::2], strict=False):
        if content.strip():
            sections.append(Section(heading, content.strip()))
    doc_type = "policy" if path.stem == "approved_answers" else "meta"
    return Document(
        document_id=f"doc-{path.stem.replace('_', '-')}", title=title, document_type=doc_type,
        source_file=str(path.relative_to(root)).replace("\\", "/"), sections=sections,
    )


def load_documents(knowledge_dir: Path) -> list[Document]:
    """Files whose names start with '_' are treated as private drafts and never loaded."""
    docs = profile_documents(load_profile(knowledge_dir))
    docs += [project_document(p) for p in load_projects(knowledge_dir)]
    md_dir = knowledge_dir / "documents"
    if md_dir.is_dir():
        docs += [markdown_document(p, knowledge_dir) for p in sorted(md_dir.glob("*.md"))
                 if not p.name.startswith("_")]
    ids = [d.document_id for d in docs]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate document_id in knowledge base")
    return [d for d in docs if d.visibility == "public"]
