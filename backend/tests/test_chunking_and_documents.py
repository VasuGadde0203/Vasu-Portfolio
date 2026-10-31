import re
from pathlib import Path

from app.rag.chunking import chunk_document, content_hash, split_text
from app.rag.documents import Document, Section, load_documents

KNOWLEDGE = Path(__file__).resolve().parents[1] / "knowledge"


def test_short_section_is_one_chunk_with_header():
    doc = Document("d1", "Title", "project", "f.json", [Section("Overview", "Short text.")], project_id="p")
    (chunk,) = chunk_document(doc, 500, 50)
    assert chunk.content == "Title — Overview\nShort text."
    assert (chunk.document_id, chunk.section, chunk.chunk_index, chunk.project_id) == ("d1", "Overview", 0, "p")
    assert chunk.content_hash == content_hash(chunk.content)


def test_long_section_splits_on_line_boundaries_with_overlap():
    text = "\n".join(f"- Line number {i} with some words" for i in range(40))
    pieces = split_text(text, 200, 40)
    assert len(pieces) > 1
    assert all(len(p) <= 200 + 40 for p in pieces)
    assert pieces[0].splitlines()[-1] in pieces[1]  # overlap carries context across the boundary


def test_very_long_single_line_is_cut():
    pieces = split_text("word " * 200, 100, 0)
    assert len(pieces) > 1 and all(len(p) <= 100 for p in pieces)


def test_chunk_indexes_are_sequential_across_sections():
    doc = Document("d", "T", "meta", "f", [Section("A", "x"), Section("B", "y"), Section("C", "z")])
    assert [c.chunk_index for c in chunk_document(doc, 500, 0)] == [0, 1, 2]


def test_chunking_is_deterministic():
    doc = Document("d", "T", "meta", "f", [Section("A", "alpha\nbeta " * 50)])
    assert chunk_document(doc, 120, 20) == chunk_document(doc, 120, 20)


def test_knowledge_base_contains_all_projects_and_core_documents():
    docs = {d.document_id: d for d in load_documents(KNOWLEDGE)}
    projects = {d.project_id for d in docs.values() if d.document_type == "project"}
    assert projects == {"invoice-extraction", "rag-chatbots", "recruitment-automation", "compliance-signals",
                        "payroll-automation", "financial-statement-extraction", "vendor-payment-management",
                        "expense-sheet-extraction", "personal-research-assistant", "gita-chatbot",
                        "class9-science-rag-chatbot", "voicebot-ai", "ai-document-analyzer",
                        "cryptolab-forecasting"}
    assert "timesnap" not in projects and "compliance-browser-automation" not in projects
    for required in ("profile", "contact", "skills", "education", "courses", "experience-jhs-associates",
                     "experience-supermoney-advisors", "career-interests", "doc-approved-answers"):
        assert required in docs


def test_private_data_is_not_in_the_knowledge_base():
    body = " ".join(s.text for d in load_documents(KNOWLEDGE) for s in d.sections)
    assert not re.search(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)", body)  # no Indian mobile number
    assert "salary" not in body.lower() or "not part of the public knowledge base" in body


def test_project_documents_keep_status_tags_and_source_urls():
    docs = {d.document_id: d for d in load_documents(KNOWLEDGE)}
    invoice = docs["project-invoice-extraction"]
    assert invoice.url == "/projects/invoice-extraction"
    arch = next(s for s in invoice.sections if s.title == "Architecture")
    assert "[unspecified]" in arch.text and "[general]" in arch.text and "[documented]" in arch.text


def test_underscore_files_are_never_loaded(tmp_path):
    import shutil
    shutil.copytree(KNOWLEDGE, tmp_path / "k")
    (tmp_path / "k" / "documents" / "_draft.md").write_text("# Secret\n\n## A\nprivate", encoding="utf-8")
    assert "doc--draft" not in {d.document_id for d in load_documents(tmp_path / "k")}
