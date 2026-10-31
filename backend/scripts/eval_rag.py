"""Live RAG evaluation against the real database and OpenAI (costs a few API calls).

    python scripts/eval_rag.py

Prints retrieval hits, similarity-score distributions (use these to tune RETRIEVAL_MIN_SCORE) and
runs full answers for the unanswerable questions, flagging metric-like numbers in the output.
A small hand-written set can reveal regressions; it does not prove complete factual accuracy.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.config import load_settings_or_exit  # noqa: E402
from app.db.session import open_session  # noqa: E402
from app.knowledge import load_profile, load_projects  # noqa: E402
from app.rag.query import HintDetector  # noqa: E402
from app.schemas.chat import ChatRequest, ChatTurn  # noqa: E402
from app.services.chat_service import ChatService  # noqa: E402
from app.services.openai_service import OpenAIService  # noqa: E402

EVAL = json.loads((BACKEND / "tests" / "eval" / "eval_set.json").read_text(encoding="utf-8"))


def main() -> int:
    s = load_settings_or_exit()
    ai = OpenAIService(s)
    detector = HintDetector(load_projects(s.knowledge_dir), load_profile(s.knowledge_dir))
    service = ChatService(s, ai, detector)
    failures = 0
    with open_session() as session:
        print(f"min_score={s.retrieval_min_score} strong_score={s.retrieval_strong_score}\n== Answerable ==")
        hits = 0
        for case in EVAL["answerable"]:
            r = service.answer(session, ChatRequest(message=case["q"]))
            ids = {x.document_id for x in r.sources}
            ok = bool(ids & set(case["expect_docs"]))
            ok_text = all(p.lower() in r.answer.lower() for p in case["must_mention"])
            hits += ok
            failures += not ok
            print(f"[{'OK ' if ok else 'MISS'}] [{r.evidence}] {case['q']}\n      sources={sorted(ids)} mentions_all={ok_text}")
        print(f"source hit rate: {hits}/{len(EVAL['answerable'])}\n\n== Unanswerable (must not invent) ==")
        for case in EVAL["unanswerable"]:
            r = service.answer(session, ChatRequest(message=case["q"]))
            bad = [p for p in EVAL["forbidden_patterns_in_answers"] if re.search(p, r.answer, re.IGNORECASE)]
            failures += bool(bad)
            print(f"[{'FLAG' if bad else 'OK  '}] {case['q']}\n      {r.answer[:220]!r}")
        print("\n== Follow-ups ==")
        for case in EVAL["follow_ups"]:
            hist = [ChatTurn(role="user", content=h) for h in case["history"]]
            r = service.answer(session, ChatRequest(message=case["q"], history=hist))
            ok = bool(r.sources) and r.sources[0].project_id == case["expect_project"]
            failures += not ok
            print(f"[{'OK ' if ok else 'MISS'}] {case['q']} -> {[x.project_id for x in r.sources]}")
    print(f"\nflagged/missed: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
