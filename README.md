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

The repo currently uses a two-track architecture:

- Core Track: stable Chroma-backed memory sidecar runtime
- Observability Track: isolated conversation/telemetry/governance subsystem under `experimental/observability/`

See `docs/architecture-tracks.md` for the current boundary.

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

## Quickstart (Core Only)

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
cp .env.example .env
make run
```

## Local Launcher (Recommended Full Stack)

Once the existing local environments are set up, you can run the full local stack
from repo root with one command:

```bash
make dev-up
```

`make dev-up` is idempotent: it ensures Core, Observability, and the UI are
running, reuses healthy services that are already up, repairs stale PID files,
and reports clear port conflicts instead of treating "already running" as a hard
failure.

Launcher prerequisites:

- Core virtualenv: `python3 -m venv .venv && source .venv/bin/activate && make setup-dev`
- Observability virtualenv: `cd experimental/observability && python3.11 -m venv .venv && ./.venv/bin/python -m pip install -e '.[dev]'`
- Web dependencies: `cd apps/web && npm ci`

This starts:

- Core on `http://127.0.0.1:8000`
- Observability on `http://127.0.0.1:8001`
- Next UI on `http://127.0.0.1:3001`

Useful companion commands:

```bash
make dev-status
make dev-logs
make dev-restart
make dev-down
```

macOS-only helper:

```bash
make dev-open
```

`make dev-open` first ensures the local stack is up, then opens the product UI.

Runtime artifacts are stored locally in `.run/`:

- PID files: `.run/*.pid`
- logs: `.run/logs/*.log`

The launcher keeps the existing manual startup flow intact and adds a simpler
repo-root path for local developer/operator use.

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
- `docs/local-stack.md`
- `docs/local-stack-minimal.md`
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

Website ops docs in this repo live under:

- `docs/domain-operations.md`
- `docs/website-routing.md`
- `infra/cloudflare/`

A local-only static website worktree may also exist at:

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
make web-check
```

CI runs:

- core lint + tests
- web lint + typecheck + build when `apps/web` is present
- observability tests in a separate workflow when `experimental/observability/**` changes

## Operations

- Runbook: `docs/operator-runbook.md`
- Release checklist: `docs/release-checklist.md`
- Changelog: `CHANGELOG.md`

## License

MIT
