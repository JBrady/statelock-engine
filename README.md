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
- `examples/litellm-client/`

For a quick end-to-end test with OpenClaw `/memory_query`, use the "Save a test memory" section in:

- `docs/run-with-local-first-stack.md`

## Development

```bash
make lint
make test
```

CI runs both lint and tests.

## License

MIT
