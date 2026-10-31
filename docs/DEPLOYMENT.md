# Deployment and operations

> Nothing here has been deployed from this repository yet. Treat the steps as a checklist, and
> do not consider the production chatbot working until you complete step 9.

## 1. Local development
See the README quick start. Test database for integration tests:

```bash
docker exec vasu-pgvector psql -U portfolio -d postgres -c "CREATE DATABASE portfolio_test"
cd backend && pytest            # integration tests use TEST_DATABASE_URL, default localhost:5433/portfolio_test
```

Integration tests **drop and recreate the `public` schema** of `TEST_DATABASE_URL`. Never point it at real data.

## 2. Database: Neon (free PostgreSQL with pgvector)
One Neon database holds the chatbot's vectors, the rate-limit counters **and** the contact messages (`contact_messages` table).
1. Sign up at neon.tech and create a project (pick the region closest to your backend host).
2. Open **Connect**, and copy the connection string (`postgresql://user:pass@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`).
   The app accepts it as is and rewrites the scheme for psycopg 3. The direct host and the `-pooler` host both work.
3. Put it in `DATABASE_URL` (backend host env vars, and `backend/.env` when running migrations or ingestion from your machine).
4. Run the migrations; the first one runs `CREATE EXTENSION IF NOT EXISTS vector`, which Neon allows:
   `cd backend && alembic upgrade head`
5. Ingest the knowledge base (step 4 below), then read your messages any time in the Neon SQL editor:
   `SELECT created_at, name, email, message FROM contact_messages ORDER BY created_at DESC;`
6. Free-plan limits (storage, compute hours, scale-to-zero after idle, so the first request after a pause is slower) change over time; check neon.tech/pricing.
   The knowledge index is reproducible with `python -m app.rag.ingest`.

## 3. Migrations
The container's start command runs `alembic upgrade head` on every boot (idempotent). Manually:

```bash
cd backend && DATABASE_URL=... alembic upgrade head
alembic downgrade -1          # roll back one revision
```

## 4. Knowledge ingestion
Ingestion is intentionally **not** run at server start. Run it from your machine against the production `DATABASE_URL`
(or `railway run python -m app.rag.ingest`):

```bash
cd backend && python -m app.rag.ingest --dry-run   # shows what would change; no API calls or writes
python -m app.rag.ingest                           # idempotent; unchanged chunks are not re-embedded
python -m app.rag.ingest --force-reembed           # after changing OPENAI_EMBEDDING_MODEL
```

Each run is recorded in `ingestion_runs` (status, counts, error). Writes happen in a single transaction after all embeddings succeed.

**Changing embedding model:** same dimensions (e.g. another 1536-d model, or a `text-embedding-3-*` model, which the code requests at 1536 via the `dimensions` parameter): change `OPENAI_EMBEDDING_MODEL` and run ingestion; old-model vectors are never searched. Different native dimensions: add a migration altering the `vector(N)` column, update `VECTOR_DIMENSIONS` in `app/db/models.py`, and re-embed everything.

## 5a. Backend on Vercel (free; pairs with Neon, so the whole app lives on Vercel + Neon)
> Prepared but **not yet tested on Vercel** (no deployment has been made from this repository). Check the first deploy against step 9.
1. Vercel → **Add New → Project** → import the same GitHub repo a second time. Set **Root Directory = `backend`**. Vercel detects FastAPI from `backend/index.py` (it exposes the ASGI `app`); `backend/vercel.json` sets a 30 s function limit and `backend/.vercelignore` keeps tests, the virtualenv and secrets out of the bundle.
2. Environment variables (Project → Settings → Environment Variables), the same ones as in section 8: `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL` (the Neon string), `ENVIRONMENT=production`, `TRUST_PROXY_HEADERS=true`, `ALLOWED_ORIGINS` (the **frontend's** Vercel URL, exact, no trailing slash).
3. Migrations and ingestion are **not** run by Vercel. Run them once from your machine against the Neon `DATABASE_URL` (sections 3 and 4), and again after changing knowledge files.
4. Deploy. Then `GET https://<backend>.vercel.app/api/health` should return `{"status":"ok"}` and `/api/health/ready` should return ready.
5. In the **frontend** project set `VITE_API_BASE_URL=https://<backend>.vercel.app` and redeploy it.
Trade-offs of serverless: the first request after idle is slower (cold start), each request is stateless (rate limits and contact messages already live in PostgreSQL, so nothing is lost), and a chat request must finish within the function time limit (a normal answer takes a few seconds). The Hobby plan's limits and terms (including non-commercial use) are Vercel's to change; check vercel.com/pricing.

## 5. Backend on Railway (alternative; not free beyond trial credit)
Railway can host the whole app: the backend service from the `backend/Dockerfile`, plus the frontend as a second service or still on Vercel.
1. New service from this repo, **root directory `backend`**; Railway detects the `Dockerfile`.
2. Variables (see `backend/.env.example`): `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `DATABASE_URL` (reference the database service variable),
   `ENVIRONMENT=production`, `ALLOWED_ORIGINS` (exact Vercel origin(s), comma-separated, no wildcard), `TRUST_PROXY_HEADERS=true`, `RATE_LIMIT_PER_MINUTE`.
   Use a standard (non-reasoning) chat model; reasoning models can spend the output-token budget before answering and return an empty response (handled as a safe error, but useless).
3. Health check path: `/api/health` (liveness). `/api/health/ready` also verifies DB, pgvector, schema, dimensions and that knowledge is indexed (returns 503 until ingestion has run). Do not expose any other diagnostics.
4. In production the app disables `/docs` and `/openapi.json`.
5. Startup fails fast with a readable list of missing/invalid variables.

## 6. Frontend on Vercel
1. Import the repo, **root directory `frontend`**, framework Vite (`vercel.json` already sets build, output and SPA rewrites).
2. Variable: `VITE_API_BASE_URL=https://<your-railway-domain>` (no trailing slash). Only `VITE_` variables reach the browser; never add secrets.
3. Optional `SITE_URL` for the sitemap. After frontend data changes, run `python backend/scripts/sync_frontend_data.py` and commit `frontend/src/data/generated/`.
4. `public/Vasu_Resume.pdf` is the downloadable resume. Replace it to update.

## 7. CORS
`ALLOWED_ORIGINS` on the backend must contain the exact Vercel production URL (and a custom domain if you add one). Preview deployments need their origin added or they will be blocked (that is intended).

## 8. Environment variable reference
| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL` | Required. Model names are never hardcoded. |
| `OPENAI_TIMEOUT` (30), `OPENAI_MAX_OUTPUT_TOKENS` (600), `OPENAI_EMBEDDING_BATCH_SIZE` (64), `OPENAI_MAX_RETRIES` (2) | Cost/latency bounds |
| `DATABASE_URL` | Required |
| `ALLOWED_ORIGINS`, `ENVIRONMENT`, `TRUST_PROXY_HEADERS` | HTTP behaviour |
| `RATE_LIMIT_PER_MINUTE` (10), `RATE_LIMIT_PER_DAY` (150) | Per-client limits, stored in PostgreSQL so they hold across instances (no Redis needed). |
| `CONTACT_RATE_LIMIT_PER_HOUR` (5) | Per-client limit for the contact form (PostgreSQL counters). Messages are stored in the `contact_messages` table of `DATABASE_URL`, so no extra service is needed. |
| `MAX_MESSAGE_CHARS` (600), `MAX_HISTORY_MESSAGES` (6) | Request limits |
| `RETRIEVAL_TOP_K`, `RETRIEVAL_MIN_SCORE`, `RETRIEVAL_STRONG_SCORE`, `MAX_CONTEXT_CHARS` | Retrieval tuning |
| `VITE_API_BASE_URL` (frontend) | Backend URL |

## 9. Testing the production chatbot
1. `GET https://<backend>/api/health` → `{"status":"ok"}`; `GET /api/health/ready` → `ready`.
2. From the Vercel site, open the chat and try each suggested question; confirm sources appear and links work.
3. Ask a follow-up ("What did he use for OCR?") after the invoice question.
4. Ask "What was the exact accuracy of his invoice extraction system?" — it must decline to give a number.
5. Hit the endpoint repeatedly to confirm 429 responses; check Railway logs contain no keys or chat text.
6. Run `python backend/scripts/eval_rag.py` with production-like settings and tune `RETRIEVAL_MIN_SCORE`.

## 10. Updating after changing a project
Edit `backend/knowledge/projects/<id>.json` → `python backend/scripts/sync_frontend_data.py` → `python -m app.rag.ingest` → push. Re-running ingestion embeds only the changed sections.

## Cost drivers
- **Query embeddings:** one tiny embedding call per visitor question.
- **Chat completions:** the main variable cost; bounded by `RETRIEVAL_TOP_K`, `MAX_CONTEXT_CHARS`, `OPENAI_MAX_OUTPUT_TOKENS`, the history cap, and rate limits. Questions with no relevant evidence skip the chat call entirely.
- **Ingestion:** the current knowledge base is 113 chunks, embedded in 2 batched requests, and only when content changes.
- **Database hosting:** a small PostgreSQL instance; the vector data is tiny.
No response caching layer is included because question diversity is high and the benefit is unproven.

## Security notes
OpenAI key and DB credentials are server-side only and never logged; errors to visitors are generic; CORS is an explicit allow-list; bodies are size-limited; inputs are validated;
all SQL is parameterised via SQLAlchemy; private (`visibility != public`) chunks and `_`-prefixed files are never retrievable; the model has no tools; chat is not stored.
Residual risks: prompt injection can never be fully eliminated for an LLM (the design limits impact to a wrong or off-topic answer, with no secrets or actions reachable);
a determined attacker can rotate IPs to evade per-IP limits, so set an OpenAI spend limit on the key.
