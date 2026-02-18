# StateLock Engine

StateLock Engine is a **self-hosted memory sidecar API** for local-first AI systems.

It is designed to pair with:

- **Ollama** for local inference
- **LiteLLM** for model alias routing/fallback
- **OpenClaw** (or other agents) for tool execution

StateLock handles memory persistence/retrieval. It does **not** route model calls.

## Architecture Role

- Inference routing: LiteLLM
- Agent runtime: OpenClaw
- Durable memory: StateLock

## Features

- Session-scoped memory blocks (`session_id`)
- CRUD and semantic query APIs
- Hybrid query endpoint (`/memories/query-hybrid`) with recency + similarity scoring
- Idempotent upsert (`/memories/upsert`) with deterministic IDs
- Session snapshot/restore endpoints
- Structured error responses with `code`, `message`, `details`, `trace_id`
- Response headers:
  - `X-Trace-Id`
  - `X-Statelock-Version`
  - `X-Statelock-Version-Requested` (echoed when request provides `X-Statelock-Version`)
- Optional API auth (`X-Statelock-Api-Key`) controlled by env
- Health endpoints (`/healthz`, `/readyz`)

## Quickstart (Local)

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
cp .env.example .env
make run
```

API docs:

- `http://127.0.0.1:8000/docs`

## Quickstart (Docker)

```bash
cp .env.example .env
make up
```

## Core Endpoints

- `POST /memories/`
- `POST /memories/upsert`
- `POST /memories/query`
- `POST /memories/query-hybrid`
- `GET /memories/?session_id=...&limit=...&offset=...`
- `DELETE /memories/{id}`
- `DELETE /memories/session/{session_id}`
- `DELETE /memories/bulk`
- `GET /memories/session/{session_id}/snapshot`
- `POST /memories/session/{session_id}/restore`
- `GET /healthz`
- `GET /readyz`
- `GET /stats/overview`
- `GET /sessions?limit=...&offset=...`
- `GET /tags?limit=...&offset=...`

## Session ID Convention

Recommended format for agent integrations:

`{channel}:{thread_or_chat}:{user_or_agent}`

Example:

`telegram:chat_12345:user_987`

## Local-First Stack Integration

See:

- `docs/run-with-local-first-stack.md`
- `examples/openclaw-tooling/`
- `examples/openclaw-tooling/openclaw-runtime/`
- `examples/openclaw-tooling/AUTOMATION_CONTRACT.md`
- `examples/litellm-client/`

## Memory Console (Local)

When running the API locally, a local-only UI is available at:

- `http://127.0.0.1:8000/app`

The console supports:

- auth shell (`API base`, `API key`)
- memory explorer and operations
- query and hybrid query workbench
- snapshot export/restore
- diagnostics panel (trace/version headers + structured errors)

For a quick end-to-end test with OpenClaw `/memory_query`, use the "Save a test memory" section in:

- `docs/run-with-local-first-stack.md`

## Domain and Website Ops

Cloudflare domain strategy, redirect policy, and DNS/email templates:

- `docs/domain-operations.md`
- `docs/website-routing.md`
- `infra/cloudflare/redirects.csv`
- `infra/cloudflare/dns-template.md`

## Website (Static v1)

The public website lives in:

- `site/`

Key routes shipped in v1:

- `/` (landing page)
- `/docs`
- `/install`
- `/github` (redirect)
- `/changelog` (redirect)

Cloudflare Pages deployment defaults:

- Build command: none
- Output directory: `site`

## Development

```bash
make lint
make test
```

CI runs both lint and tests.

## Operations

- Runbook: `docs/operator-runbook.md`
- Release checklist: `docs/release-checklist.md`
- Changelog: `CHANGELOG.md`

## License

MIT
