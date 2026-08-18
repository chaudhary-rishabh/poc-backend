# AI Business Discovery to POC — Backend

FastAPI service that turns scattered client inputs (files, pasted text, screenshots) into a structured business discovery report, a UX/flow document, an architecture document, and a small interactive POC mockup — with a human approval gate and human-in-the-loop editing at every stage.

## Flow

```
Ingest (files / text / screenshots)
        │
        ▼
Discovery Report (Doc A)  ──► Human approval / regenerate
        │  (locked)
        ▼
UX & Flow Doc (Doc B)
        │
        ▼
Architecture Doc (Doc C)
        │
        ▼
POC (interactive frontend-only mockup)
```

Each stage's output is Pydantic-validated before it's persisted or returned. Doc B is generated from locked Doc A only; Doc C from locked Doc A + Doc B; the POC is template-filled from Doc B (Doc C is documentation-only, not wired to a live backend — see **Assumptions**).

## Human-in-the-loop

Every stage (Doc A, Doc B, Doc C, POC) supports feedback-driven regeneration, not just a blind "start over":

- `POST /session/{id}/chat` — the single entry point for "fix this" style edits from the main chat input. Takes a `target_doc` and a `message`, routes to the correct regeneration path, and includes the **current version of that doc** alongside the feedback in the prompt, so the model edits the existing output rather than regenerating from scratch.
- If a document is edited after downstream documents already exist (e.g. Doc B changes after Doc C/POC were generated), the response includes `stale_downstream` so the client can flag out-of-date artifacts without auto-regenerating them.

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + `asyncpg` |
| Database | PostgreSQL (Neon) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Config | `pydantic-settings` |
| PDF parsing | `pypdf` |
| LLM — Anthropic | `anthropic` SDK |
| LLM — DeepSeek | `openai` SDK (OpenAI-compatible endpoint) |
| Containerization | Docker (multi-stage, non-root) |
| Deployment | Google Cloud Run |

## AI providers

Both Anthropic and DeepSeek are supported behind one `LLMProvider` interface, selected **per request** via a `provider` field (not just an env-level default) — the frontend's model switcher controls this directly. Screenshot-to-text always uses Anthropic's vision call regardless of the selected text provider, since DeepSeek's API does not accept image input.

Every LLM call is schema-validated; on a validation failure it retries once with the error fed back into the prompt before failing with a 502.

## API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /ingest` | Parse files/text/screenshots into combined session text |
| `POST /discovery` | Generate Doc A |
| `POST /approve/doc-a` | Lock or regenerate Doc A |
| `POST /generate/doc-b` | Generate Doc B from locked Doc A |
| `POST /generate/doc-c` | Generate Doc C from locked Doc A + B |
| `POST /generate/poc` | Generate the POC from Doc B |
| `POST /session/{id}/chat` | Human-in-the-loop feedback routing to any of the above |
| `GET /session/{id}` | Full session state |
| `GET /sessions` | List all sessions (for the projects/sidebar view) |
| `PATCH /session/{id}` | Rename a session |
| `DELETE /session/{id}` | Delete a session |

Interactive docs at `/docs` (Swagger UI).

## Running locally

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt --break-system-packages

cp .env.example .env       # fill in DATABASE_URL, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

## Environment variables

```
DATABASE_URL           # Neon pooled connection string
DATABASE_URL_DIRECT     # Neon direct connection string, Alembic only
LLM_PROVIDER            # default provider if not specified per-request
FRONTEND_ORIGIN         # CORS — the deployed frontend's URL
ANTHROPIC_API_KEY
DEEPSEEK_API_KEY
```

## Deployment

Built via Docker (multi-stage, non-root user, binds to Cloud Run's dynamic `$PORT`), deployed to Google Cloud Run via Artifact Registry:

```bash
gcloud builds submit --tag <region>-docker.pkg.dev/<project>/<repo>/backend:latest
gcloud run deploy ai-discovery-backend --image <same tag> --region <region> --allow-unauthenticated
```

## Assumptions

- Single-user context — no authentication. Not intended as multi-tenant.
- The POC is frontend-only: it demonstrates the UX interactively using in-memory state, but is not wired to a live backend or database. Doc C fully documents the intended schema, API routes, and tech stack a real implementation would use — building and sandboxing that live backend was treated as out of scope for a one-week exercise, per the assignment brief's own framing.
- Website scraping was not implemented as an input type; the brief listed it as optional and files/text/screenshots were treated as sufficient coverage of the three-input-type requirement.
- Regeneration with feedback overwrites the previous draft rather than keeping a version history — acceptable for this scope, not intended as a production audit trail.