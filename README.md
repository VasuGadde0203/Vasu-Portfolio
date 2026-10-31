# Vasu Gadde — Portfolio + "Ask Vasu AI" (RAG)

A React/TypeScript portfolio with a FastAPI backend that answers visitor questions using real
Retrieval-Augmented Generation: OpenAI embeddings, PostgreSQL + pgvector, and an OpenAI chat model
constrained to retrieved, approved knowledge.

```
Visitor → Vercel (React) → Railway (FastAPI) ─┬→ OpenAI (embeddings + chat)
                                               └→ PostgreSQL + pgvector
```

## Repository layout

| Path | Purpose |
|---|---|
| `backend/knowledge/` | **Canonical source of truth.** `profile.json`, `projects/*.json`, `documents/*.md` |
| `backend/app/` | FastAPI app: `api/`, `core/` (config, security, logging), `db/`, `rag/`, `services/`, `schemas/` |
| `backend/alembic/` | Database migrations (creates the `vector` extension and tables) |
| `backend/tests/` | Unit + integration tests, `tests/eval/eval_set.json` |
| `backend/scripts/` | `sync_frontend_data.py`, `eval_rag.py` (live evaluation) |
| `frontend/` | Vite + React + TypeScript + Tailwind. `src/data/generated/` is generated from the knowledge files |
| `docs/DEPLOYMENT.md` | Local setup, Railway, Vercel, operations, cost, security notes |

## Quick start (local)

Prerequisites: Python 3.11+, Node 20+, Docker (for PostgreSQL + pgvector), an OpenAI API key.

```bash
docker run -d --name vasu-pgvector -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=portfolio -e POSTGRES_USER=portfolio -p 5433:5432 pgvector/pgvector:pg16
```

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                             # then fill OPENAI_API_KEY and OPENAI_CHAT_MODEL
alembic upgrade head                             # create schema
python -m app.rag.ingest                         # embed the knowledge base (a few API calls)
uvicorn app.main:app_factory --factory --reload --port 8000
```

```bash
cd frontend
cp .env.example .env                             # VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev                                      # http://localhost:5173
```

## Updating content (the one workflow)

1. Edit the canonical files in `backend/knowledge/` (`profile.json`, `projects/<id>.json`, `documents/*.md`).
   Files starting with `_` are treated as private drafts and are never loaded or ingested.
2. `python backend/scripts/sync_frontend_data.py` — regenerates the frontend's typed data
   (`--check` fails if it is stale; use it in CI).
3. `python -m app.rag.ingest` (from `backend/`) — re-embeds **only changed chunks**; removed documents are pruned.
4. Commit and deploy. Adding a project is a new JSON file; no retrieval or UI code changes are needed
   (routes, cards, filters and RAG documents are all driven by the data).

Contact settings live in `profile.json → contact`: `linkedin`, `github`, `resume_url`, `show_location`,
and `phone` + `show_phone` (phone is private by default and is not in the public data or knowledge base).

## How the RAG pipeline works

`POST /api/chat` → validate (Pydantic, length and history limits) → per-client rate limit (PostgreSQL counters, works across
instances) → resolve follow-ups from the visitor's previous question and detect the project being discussed → embed
**only that one query** → exact cosine search in pgvector (public chunks, current embedding model only) with a similarity
threshold, project boost, per-document cap and a context character budget → if nothing relevant, return an honest fallback
**without calling the chat model** → otherwise send the bounded context to the chat model with grounding rules → parse `[n]`
citation markers, return only sources that were retrieved and cited.

Design decisions worth knowing:
- **No vector index.** The corpus is ~113 chunks, so an exact scan is faster and more accurate than HNSW. The migration notes when to add one.
- **Embedding model changes are explicit.** Chunks store `embedding_model`; retrieval only compares vectors from the configured model and ingestion re-embeds the rest. The column is fixed at 1536 dimensions and `EMBEDDING_DIMENSIONS` is validated against it at startup and in `/api/health/ready`.
- **Status tags in project knowledge** (`documented` / `general` / `unspecified`) travel into the prompt so the model can distinguish verified facts from general reasoning.
- **Prompt-injection stance:** visitor text, history and retrieved chunks are all untrusted; the model has no tools and no secrets, and output is rendered as safe Markdown (no raw HTML, restricted links).

## Verification status (what was actually run)

| Check | Result |
|---|---|
| Backend unit + integration tests (`pytest`) | 71 passed, 2 skipped (the opt-in live-OpenAI module and one eval case that needs real embeddings) against real PostgreSQL 16 + pgvector 0.8.7 (`pgvector/pgvector:pg16`) |
| Alembic migration up/down/up on real pgvector | Passed (part of the integration tests) |
| Idempotent ingestion, changed-chunk-only re-embedding, model-change re-embed, rollback on failure | Passed with a deterministic fake embedder |
| Vector similarity SQL, visibility filter, project filter | Passed on real pgvector |
| `ruff`, `mypy` (backend) | Clean |
| Frontend `tsc` strict, `vitest` (9 tests), production `vite build` | Passed |
| Docker image build; container boots, runs migrations, serves `/api/health` | Passed |
| Browser → FastAPI → real OpenAI SDK with an **invalid** key | Verified: safe "temporarily unavailable" message with Retry, no key/detail leakage |
| Desktop and 375px mobile rendering, direct navigation to `/projects/invoice-extraction` | Checked visually |

**Verified with the real OpenAI API** (`text-embedding-3-small` + `gpt-4o-mini`, local pgvector): ingestion embedded 113 chunks, a second run
re-embedded 0; `scripts/eval_rag.py` gave 7/8 expected-source hits on the first run (the miss was an over-narrow expectation, since fixed),
all 5 unanswerable questions declined to give a figure with no invented numbers, and both follow-ups resolved to the right project.
This is a small set run once: it shows the pipeline works, not that every answer is accurate. Thresholds are still defaults, not tuned.

**Not verified — needs your deployment accounts:**
- Wider answer quality beyond the 15-question eval set, and threshold tuning (`RETRIEVAL_MIN_SCORE=0.30` / `RETRIEVAL_STRONG_SCORE=0.45`).
- The integration tests use a lexical fake embedder, so they prove plumbing and SQL, not semantic relevance. One eval question
  ("cloud deployment technologies") needs real embeddings and is skipped in the automated run.
- Real OpenAI calls: `TEST_LIVE_OPENAI=1 pytest -m openai_live`.
- Railway and Vercel deployments have **not** been performed. `docs/DEPLOYMENT.md` has the exact steps and a checklist.
- Hosted pgvector on Railway: use Railway's pgvector-enabled PostgreSQL template/image and confirm `CREATE EXTENSION vector` succeeds (migration 0001 does this); not tested there.
- The eval set is small (8 answerable, 5 unanswerable, 2 follow-ups). It catches regressions; it does not prove factual accuracy.

## Known limitations and decisions to review

- **LinkedIn and GitHub URLs** were read from the hyperlinks embedded in `Vasu_Resume.pdf`
  (`linkedin.com/in/vasu-gadde`, `github.com/VasuGadde0203`) because the resume text only shows the words. Please confirm they are correct, or set them to `null`.
- **The public resume PDF contains your phone number** (it is in the PDF itself). The site never prints it, but anyone can download the PDF. Consider uploading a version without the phone number as `frontend/public/Vasu_Resume.pdf`.
- Skill labels (`Professional experience` / `Used in documented projects` / `Familiar with`) are my reading of the resume. Review `profile.json → skills`.
  AWS, Docker and GitHub Actions are "Familiar with" because your resume says so; Docker/AWS deployment is also noted from the internship bullet.
- The RAG-Based Chatbot Systems and Recruitment Automation projects are not attributed to an employer, because the resume does not attribute them.
- "Possible future improvements" on project pages are my suggestions, labelled as possibilities. Delete or edit any you do not endorse.
- Career interests are derived only from your title and focus areas; no compensation or location preferences are stated.
- No light theme and no contact form (a `mailto:` link is used instead of a form with no delivery backend). No dedicated `/assistant` page; the chat is a widget plus the hero button.
- Chat history is client-memory only and is never stored server-side. Rate limiting uses PostgreSQL (shared across instances) keyed by hashed client IP; set `TRUST_PROXY_HEADERS=true` behind Railway.
- Frontend chat limits (`600` chars / `6` history messages) mirror backend defaults; if you change `MAX_MESSAGE_CHARS` / `MAX_HISTORY_MESSAGES`, update `frontend/src/lib/api.ts`.
- Sitemap/robots are generated at build time from `SITE_URL` (or Vercel's production URL); without either, no sitemap is emitted rather than inventing a domain. No Open Graph image is provided.
