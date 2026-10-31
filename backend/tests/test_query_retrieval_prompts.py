import httpx
import openai
import pytest

from app.db.repositories import ScoredChunk
from app.knowledge import load_profile, load_projects
from app.rag.citations import (
    build_sources,
    extract_cited_indexes,
    project_links,
    remove_unverified_links,
    strip_markers,
)
from app.rag.prompts import SYSTEM_PROMPT, build_messages, format_context
from app.rag.query import HintDetector, Hints, is_follow_up, normalize_query, resolve_query
from app.rag.retrieval import assess_evidence, rank_and_select
from app.schemas.chat import ChatTurn
from app.services.errors import ServiceError
from app.services.openai_service import translate_openai_error, validate_dimensions


def _projects():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "knowledge"
    return {p.id: p for p in load_projects(root)}


def test_invented_links_are_removed_and_verified_ones_are_appended():
    answer = ("See the [Invoice case study](/projects/ai-invoice-pdf-extraction) and "
              "[repo](https://github.com/voicebot-ai), also https://evil.example/x and /projects/invoice-extraction.")
    cleaned = remove_unverified_links(answer, allowed={"https://github.com/VasuGadde0203"})
    assert "(/projects" not in cleaned and "github.com/voicebot-ai" not in cleaned
    assert "evil.example" not in cleaned and "/projects/" not in cleaned
    assert "Invoice case study" in cleaned and "repo" in cleaned  # labels are kept as plain text
    assert "https://github.com/VasuGadde0203" in remove_unverified_links(
        "Profile: https://github.com/VasuGadde0203.", {"https://github.com/VasuGadde0203"})


def test_project_links_use_real_ids_and_real_github_urls_only():
    projects = _projects()
    one = project_links(["voicebot-ai"], projects)
    assert "(/projects/voicebot-ai)" in one and "https://github.com/VasuGadde0203/My-Voicebot-AI" in one
    many = project_links(["invoice-extraction", "gita-chatbot", "made-up-id", "voicebot-ai", "cryptolab-forecasting"], projects)
    assert "made-up-id" not in many and many.count("(/projects/") == 3  # capped, unknown ids skipped
    assert project_links(["invoice-extraction"], projects).count("github.com") == 0  # employer project: no repo link
    assert project_links([], projects) == ""


def chunk(doc="d", idx=0, score=0.5, project=None, content="text", section="S", h=None):
    return ScoredChunk(doc, f"Title {doc}", "project", project, section, idx, content, h or f"{doc}{idx}", f"/x/{doc}", score)


# ---- query handling ------------------------------------------------------------------------
def test_normalize_strips_control_chars_and_whitespace():
    assert normalize_query("  hello \x00\x07  world\n\n there ") == "hello world there"


def test_follow_up_detection_and_resolution():
    history = [ChatTurn(role="user", content="Explain Vasu's invoice processing project."),
               ChatTurn(role="assistant", content="It uses Surya OCR and Qwen2.5.")]
    assert is_follow_up("What did he use for OCR?")
    assert "invoice processing" in resolve_query("What did he use for OCR?", history)
    standalone = "Describe the complete architecture of the compliance signals tool in detail please"
    assert not is_follow_up(standalone)
    assert resolve_query(standalone, history) == standalone


def test_resolution_ignores_assistant_turns():
    history = [ChatTurn(role="assistant", content="Something unverified about FAISS")]
    assert resolve_query("and what about it?", history) == "and what about it?"


@pytest.fixture(scope="module")
def detector():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "knowledge"
    return HintDetector(load_projects(root), load_profile(root))


def test_project_detection_from_message_and_history(detector):
    assert detector.detect("Tell me about his recruitment automation platform", []).project_id == "recruitment-automation"
    assert detector.detect("How does the hybrid OCR pipeline work?", []).project_id == "invoice-extraction"
    history = [ChatTurn(role="user", content="Explain his invoice processing project")]
    assert detector.detect("What did he use for OCR?", history).project_id == "invoice-extraction"
    assert detector.detect("Where is he based?", []).project_id is None


def test_technology_detection(detector):
    assert "FastAPI" in detector.detect("What is his experience with FastAPI?", []).technologies
    assert detector.detect("Hello there", []).technologies == []


# ---- ranking, thresholds, context -------------------------------------------------------------
def test_threshold_drops_irrelevant_and_empty_result_is_none(settings):
    assert rank_and_select([chunk(score=0.01)], Hints(None, []), settings) == []
    assert assess_evidence([], settings) == "none"


def test_ranking_orders_by_score_and_assesses_evidence(settings):
    picked = rank_and_select([chunk("a", score=0.3), chunk("b", score=0.9)], Hints(None, []), settings)
    assert [c.document_id for c in picked] == ["b", "a"]
    assert assess_evidence(picked, settings) == "strong"
    assert assess_evidence([chunk(score=0.1)], settings) == "partial"


def test_project_boost_prefers_the_asked_about_project(settings):
    cands = [chunk("other", 0, 0.50), chunk("proj", 0, 0.47, project="invoice-extraction")]
    picked = rank_and_select(cands, Hints("invoice-extraction", []), settings)
    assert picked[0].document_id == "proj"


def test_duplicates_are_removed(settings):
    cands = [chunk("a", 0, 0.9), chunk("a", 0, 0.9), chunk("b", 1, 0.8, h="a0")]
    assert len(rank_and_select(cands, Hints(None, []), settings)) == 1


def test_per_document_cap_and_top_k(settings):
    s = settings.model_copy(update={"retrieval_max_chunks_per_document": 2, "retrieval_top_k": 3})
    cands = [chunk("a", i, 0.9 - i * 0.01) for i in range(5)] + [chunk("b", 0, 0.5), chunk("c", 0, 0.4)]
    picked = rank_and_select(cands, Hints(None, []), s)
    assert len(picked) == 3 and sum(c.document_id == "a" for c in picked) == 2


def test_context_budget_is_respected_but_keeps_one_chunk(settings):
    s = settings.model_copy(update={"max_context_chars": 500})
    cands = [chunk("a", 0, 0.9, content="x" * 400), chunk("b", 0, 0.8, content="y" * 400)]
    assert [c.document_id for c in rank_and_select(cands, Hints(None, []), s)] == ["a"]
    big = [chunk("a", 0, 0.9, content="x" * 900)]
    assert len(rank_and_select(big, Hints(None, []), s)) == 1


# ---- prompt construction -------------------------------------------------------------------------
def test_messages_put_context_in_final_user_turn_with_history_before():
    history = [ChatTurn(role="user", content="q1"), ChatTurn(role="assistant", content="a1")]
    msgs = build_messages("q2", history, [chunk("a", content="Doc [3] text")])
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert "<context>" in msgs[-1]["content"] and "[1] Title a" in msgs[-1]["content"]
    assert "Doc (3) text" in msgs[-1]["content"]  # chunk text cannot forge citation markers
    assert msgs[-1]["content"].endswith("q2")


def test_system_prompt_contains_grounding_and_injection_rules():
    for phrase in ("untrusted", "Never invent metrics", "not the human Vasu", "ONLY from the numbered context"):
        assert phrase in SYSTEM_PROMPT
    assert "[documented]" in SYSTEM_PROMPT


def test_format_context_numbers_blocks_from_one():
    out = format_context([chunk("a"), chunk("b")])
    assert out.startswith("[1] ") and "\n\n[2] " in out


# ---- citations ----------------------------------------------------------------------------------
def test_citations_only_reference_retrieved_chunks():
    chunks = [chunk("a", 0, project="p1"), chunk("b", 0)]
    assert extract_cited_indexes("Yes [1]. Also [2][9][1].", 2) == [1, 2]  # [9] does not exist
    sources = build_sources("Yes [2].", chunks)
    assert [s.document_id for s in sources] == ["b"]
    assert strip_markers("Yes [1]. Also [2].") == "Yes. Also."


def test_abstention_produces_no_sources_but_uncited_answer_gets_top_chunk():
    chunks = [chunk("a", 0)]
    assert build_sources("I don't have a verified figure for that in my documented portfolio.", chunks) == []
    assert [s.document_id for s in build_sources("He used FastAPI.", chunks)] == ["a"]


def test_sources_are_deduplicated_by_document_and_section():
    chunks = [chunk("a", 0, section="S"), chunk("a", 1, section="S")]
    assert len(build_sources("x [1][2]", chunks)) == 1


# ---- OpenAI helpers --------------------------------------------------------------------------------
def _resp(code):
    return httpx.Response(code, request=httpx.Request("POST", "https://api.openai.com/v1/x"))


@pytest.mark.parametrize("exc,status,code", [
    (openai.AuthenticationError("secret details sk-abc", response=_resp(401), body=None), 503, "ai_unavailable"),
    (openai.RateLimitError("slow down", response=_resp(429), body=None), 429, "ai_busy"),
    (openai.APITimeoutError(httpx.Request("POST", "https://x")), 504, "ai_timeout"),
    (openai.APIConnectionError(request=httpx.Request("POST", "https://x")), 503, "ai_unavailable"),
    (openai.InternalServerError("boom", response=_resp(500), body=None), 503, "ai_unavailable"),
    (openai.BadRequestError("context length", response=_resp(400), body=None), 400, "ai_request_rejected"),
])
def test_openai_errors_are_translated_to_safe_messages(exc, status, code):
    err = translate_openai_error(exc)
    assert (err.status_code, err.code) == (status, code)
    assert "sk-" not in err.message and "secret" not in err.message


def test_embedding_dimension_validation():
    validate_dimensions([[0.0] * 4], 4)
    with pytest.raises(ServiceError, match="dimensions"):
        validate_dimensions([[0.0] * 3], 4)
