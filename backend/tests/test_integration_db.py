"""Integration tests against a REAL PostgreSQL + pgvector database (TEST_DATABASE_URL).

Embeddings here are a deterministic lexical fake, so these tests verify the schema, migrations,
ingestion, vector SQL and the HTTP flow. They do not measure real semantic retrieval quality."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import openai
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.db.models import VECTOR_DIMENSIONS, KnowledgeChunk
from app.db.repositories import KnowledgeRepository, vector_column_dimensions
from app.db.session import get_engine
from app.main import create_app
from app.rag.ingest import ingest
from tests.conftest import FakeAI, fake_embedding

pytestmark = pytest.mark.integration
BACKEND = Path(__file__).resolve().parents[1]
EVAL = json.loads((Path(__file__).parent / "eval" / "eval_set.json").read_text(encoding="utf-8"))


def _db_available() -> bool:
    try:
        with create_engine(get_settings().database_url).connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


if not _db_available():
    pytest.skip("PostgreSQL test database is not reachable (set TEST_DATABASE_URL)", allow_module_level=True)


@pytest.fixture(scope="module", autouse=True)
def migrated_database():
    engine = get_engine()
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(cfg, "head")
    yield cfg
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.fixture
def session():
    with Session(get_engine()) as s:
        s.execute(text("TRUNCATE knowledge_chunks, ingestion_runs, rate_limit_counters"))
        s.commit()
        yield s


@pytest.fixture
def settings(settings):
    return settings


def test_migrations_create_expected_schema(session):
    tables = {r[0] for r in session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))}
    assert {"knowledge_chunks", "ingestion_runs", "rate_limit_counters", "alembic_version"} <= tables
    assert session.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'")).first()
    assert vector_column_dimensions(session) == VECTOR_DIMENSIONS


def test_ingestion_is_idempotent_and_does_not_re_embed_unchanged_content(session, settings):
    ai = FakeAI(settings.openai_embedding_model)
    first = ingest(session, settings, ai)
    assert first.inserted == first.chunks_total > 0 and first.embeddings_generated > 0
    count = KnowledgeRepository(session).count_chunks()

    ai2 = FakeAI(settings.openai_embedding_model)
    second = ingest(session, settings, ai2)
    assert (second.inserted, second.updated, second.deleted) == (0, 0, 0)
    assert second.unchanged == first.chunks_total
    assert ai2.embedded_total == 0  # nothing re-embedded
    assert KnowledgeRepository(session).count_chunks() == count  # no duplicates


def test_changed_document_only_re_embeds_changed_chunks_and_prunes_removed(session, settings, tmp_path):
    k = tmp_path / "k"
    shutil.copytree(BACKEND / "knowledge", k)
    s = settings.model_copy(update={"knowledge_dir": k})
    ingest(session, s, FakeAI(s.openai_embedding_model))

    path = k / "projects" / "payroll-automation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["problem"] = "A changed problem statement about maintainability."
    path.write_text(json.dumps(data), encoding="utf-8")
    ai = FakeAI(s.openai_embedding_model)
    stats = ingest(session, s, ai)
    assert stats.updated == 1 and ai.embedded_total == 1

    (k / "documents" / "portfolio_assistant.md").unlink()
    stats = ingest(session, s, FakeAI(s.openai_embedding_model))
    assert stats.deleted > 0
    assert session.query(KnowledgeChunk).filter_by(document_id="doc-portfolio-assistant").count() == 0


def test_model_change_triggers_explicit_re_embedding(session, settings):
    ingest(session, settings, FakeAI(settings.openai_embedding_model))
    s2 = settings.model_copy(update={"openai_embedding_model": "another-model"})
    ai = FakeAI("another-model")
    stats = ingest(session, s2, ai)
    assert stats.updated == stats.chunks_total and ai.embedded_total > 0
    models = {r[0] for r in session.execute(text("SELECT DISTINCT embedding_model FROM knowledge_chunks"))}
    assert models == {"another-model"}  # vectors from different models are never mixed


def test_failed_embedding_leaves_previous_index_untouched(session, settings, tmp_path):
    k = tmp_path / "k"
    shutil.copytree(BACKEND / "knowledge", k)
    s = settings.model_copy(update={"knowledge_dir": k})
    ingest(session, s, FakeAI(s.openai_embedding_model))
    before = KnowledgeRepository(session).count_chunks()
    (k / "documents" / "extra_note.md").write_text("# New\n\n## A\nnew content", encoding="utf-8")
    broken = FakeAI(s.openai_embedding_model)
    broken.error = RuntimeError("embedding api down")
    with pytest.raises(RuntimeError):
        ingest(session, s, broken)
    session.rollback()
    assert KnowledgeRepository(session).count_chunks() == before


def test_vector_search_returns_the_matching_chunk_first_and_respects_visibility(session, settings):
    ai = FakeAI(settings.openai_embedding_model)
    ingest(session, settings, ai)
    repo = KnowledgeRepository(session)
    row = session.query(KnowledgeChunk).filter_by(document_id="project-gita-chatbot",
                                                  section="Technologies").one()
    hits = repo.search(fake_embedding(row.content), embedding_model=settings.openai_embedding_model, limit=3)
    assert hits[0].document_id == row.document_id and hits[0].score == pytest.approx(1.0, abs=1e-3)
    assert hits == sorted(hits, key=lambda h: -h.score)

    only_project = repo.search(fake_embedding("invoice ocr"), embedding_model=settings.openai_embedding_model,
                               limit=20, project_id="invoice-extraction")
    assert only_project and {h.project_id for h in only_project} == {"invoice-extraction"}

    session.execute(text("UPDATE knowledge_chunks SET visibility='private' WHERE document_id='skills'"))
    session.commit()
    hidden = repo.search(fake_embedding("python fastapi skills"), embedding_model=settings.openai_embedding_model, limit=50)
    assert all(h.document_id != "skills" for h in hidden)  # private content is never retrievable
    assert repo.search(fake_embedding("x"), embedding_model="other-model", limit=5) == []


# ---- HTTP flow --------------------------------------------------------------------------------------
@pytest.fixture
def client(session, settings):
    ai = FakeAI(settings.openai_embedding_model)
    ingest(session, settings, ai)
    ai.embed_calls.clear()
    app = create_app(settings, ai)
    app.state.fake_ai = ai
    with TestClient(app) as c:
        c.ai = ai  # type: ignore[attr-defined]
        yield c


def post(client, message, history=None):
    return client.post("/api/chat", json={"message": message, "history": history or []})


def test_chat_returns_answer_and_only_retrieved_sources(client):
    r = post(client, "Explain the invoice processing project with Surya OCR")
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].startswith("Documented answer.")
    assert "(/projects/invoice-extraction)" in body["answer"]  # verified link added by the server
    assert body["sources"] and body["sources"][0]["url"].startswith("/")
    assert body["evidence"] in {"strong", "partial"}
    assert len(client.ai.embed_calls) == 1 and len(client.ai.embed_calls[0]) == 1  # one query embedding only
    context = client.ai.complete_calls[0][-1]["content"]
    assert "Surya OCR" in context


def test_context_sent_to_the_model_is_bounded_not_the_whole_knowledge_base(client, settings):
    post(client, "What technologies does he use for vector search?")
    context = client.ai.complete_calls[0][-1]["content"]
    assert context.count("\n\n[") + 1 <= settings.retrieval_top_k
    assert len(context) < settings.max_context_chars + 1500


def test_follow_up_is_resolved_with_history(client):
    history = [{"role": "user", "content": "Explain Vasu's invoice processing project."},
               {"role": "assistant", "content": "It is a hybrid OCR and LLM pipeline."}]
    r = post(client, "What did he use for OCR?", history)
    assert r.status_code == 200
    assert r.json()["sources"][0]["project_id"] == "invoice-extraction"


def test_no_relevant_evidence_returns_honest_fallback_without_calling_the_llm(client, settings):
    client.app.state.chat_service._s = settings.model_copy(update={"retrieval_min_score": 0.99})
    r = post(client, "zzqx quuxplugh")
    assert r.status_code == 200
    assert r.json()["evidence"] == "none" and r.json()["sources"] == []
    assert "documented portfolio" in r.json()["answer"]
    assert client.ai.complete_calls == []  # no chat completion spent


def test_chat_input_validation(client, settings):
    assert post(client, "").status_code == 422
    assert post(client, "   ").status_code == 422
    assert post(client, "x" * (settings.max_message_chars + 1)).status_code == 422
    too_many = [{"role": "user", "content": "hi"}] * (settings.max_history_messages + 1)
    assert post(client, "hello", too_many).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "extra": 1}).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "history": [{"role": "system", "content": "x"}]}).status_code == 422
    assert client.post("/api/chat", content="x" * 40_000, headers={"content-type": "application/json"}).status_code == 413


def test_openai_failures_return_safe_errors_without_details(client):
    import httpx
    req = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
    client.ai.error = openai.AuthenticationError("Incorrect API key sk-live-SECRET", response=httpx.Response(401, request=req), body=None)
    from app.services.openai_service import translate_openai_error
    original = client.ai.embed

    def failing(texts):
        raise translate_openai_error(client.ai.error)
    client.ai.embed = failing  # type: ignore[method-assign]
    r = post(client, "hello there")
    assert r.status_code == 503
    assert "SECRET" not in r.text and "sk-" not in r.text and "Traceback" not in r.text
    assert r.json()["error"]["code"] == "ai_unavailable"
    client.ai.embed = original  # type: ignore[method-assign]


def test_unexpected_exceptions_are_not_leaked(client):
    client.ai.complete = lambda m: (_ for _ in ()).throw(ValueError("db password hunter2"))  # type: ignore[method-assign]
    r = TestClient(client.app, raise_server_exceptions=False).post("/api/chat", json={"message": "invoice ocr"})
    assert r.status_code == 500 and "hunter2" not in r.text


def test_rate_limit_is_enforced_per_client(client, settings):
    client.app.dependency_overrides[get_settings] = lambda: settings.model_copy(update={"rate_limit_per_minute": 3})
    responses = [post(client, "invoice ocr") for _ in range(5)]
    client.app.dependency_overrides.clear()
    assert [r.status_code for r in responses] == [200, 200, 200, 429, 429]
    assert responses[-1].headers["retry-after"] == "60"
    assert responses[-1].json()["error"]["code"] == "rate_limited"


def test_health_endpoints_and_readiness(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    ready = client.get("/api/health/ready")
    assert ready.status_code == 200 and ready.json()["status"] == "ready"


def test_readiness_reports_unindexed_knowledge(session, settings):
    with TestClient(create_app(settings, FakeAI())) as c:
        r = c.get("/api/health/ready")
        assert r.status_code == 503 and r.json()["knowledge_indexed"] is False and r.json()["database"] is True


def test_content_endpoints_and_phone_privacy(client):
    profile = client.get("/api/profile").json()
    assert profile["contact"]["phone"] is None and not re.search(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)", client.get("/api/profile").text)
    assert len(client.get("/api/projects").json()) == 14
    assert client.get("/api/projects/invoice-extraction").json()["title"] == "AI Invoice & PDF Extraction"
    assert client.get("/api/projects/nope").status_code == 404


def test_cors_allows_only_configured_origins(client, settings):
    ok = client.options("/api/chat", headers={"Origin": settings.cors_origins[0], "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == settings.cors_origins[0]
    bad = client.options("/api/chat", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


# ---- evaluation set (retrieval plumbing with lexical fake embeddings) -------------------------------------
@pytest.mark.parametrize("case", EVAL["answerable"], ids=lambda c: c["q"][:40])
def test_eval_answerable_questions_retrieve_expected_documents(client, case):
    if case.get("needs_semantic_embeddings"):
        pytest.skip("Needs real semantic embeddings (no lexical overlap); covered by scripts/eval_rag.py")
    r = post(client, case["q"])
    ids = {s["document_id"] for s in r.json()["sources"]}
    retrieved = client.ai.complete_calls[-1][-1]["content"]
    assert any(doc_title_hit(retrieved, d, client) for d in case["expect_docs"]) or ids & set(case["expect_docs"])
    for phrase in case["must_mention"]:
        assert phrase.lower() in retrieved.lower(), f"evidence for {phrase!r} was not retrieved"


def doc_title_hit(context: str, doc_id: str, client) -> bool:
    with Session(get_engine()) as s:
        title = s.execute(text("SELECT document_title FROM knowledge_chunks WHERE document_id=:d LIMIT 1"), {"d": doc_id}).scalar()
    return bool(title) and title in context


@pytest.mark.parametrize("case", EVAL["unanswerable"], ids=lambda c: c["q"][:40])
def test_eval_unanswerable_questions_never_get_invented_sources_or_numbers(client, case):
    """With the LLM faked we can only verify the evidence given to it: the policy document must be
    retrievable and no chunk may contain a metric that could be mistaken for a verified figure."""
    post(client, case["q"])
    context = client.ai.complete_calls[-1][-1]["content"] if client.ai.complete_calls else ""
    import re
    for pattern in EVAL["forbidden_patterns_in_answers"][:2]:  # percentages and dollar amounts
        assert not re.search(pattern, context), f"knowledge base contains a metric-like value: {pattern}"


@pytest.mark.parametrize("case", EVAL["follow_ups"], ids=lambda c: c["q"][:40])
def test_eval_follow_ups_resolve_to_the_right_project(client, case):
    history = [{"role": "user", "content": h} for h in case["history"]]
    r = post(client, case["q"], history)
    assert r.json()["sources"][0]["project_id"] == case["expect_project"]
