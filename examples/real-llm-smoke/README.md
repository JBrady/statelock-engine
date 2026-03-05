# Real LLM Smoke Test (Core Track)

This example proves an end-to-end local-first flow against **StateLock Core**:
1. call a real LLM backend,
2. save assistant output to StateLock memory,
3. retrieve it via Core query API,
4. emulate working-context assembly in the script,
5. call the LLM again with that context.

## Track Boundary

This example uses only Core Track endpoints (`/memories/*`) and does not use or wire Observability Track.

Core Track does not provide a working-context endpoint, so context assembly is intentionally emulated in the script.

## Prerequisites

1. StateLock Core API running locally.
2. At least one LLM path available:
- LiteLLM (`/v1/chat/completions`), or
- Ollama (`/api/generate`), or
- OpenAI (only when both `OPENAI_API_KEY` and `OPENAI_MODEL` are set).

## Python Environment Checks

Run these first to avoid interpreter confusion:

```bash
which python
python -V
python -c "import sys; print(sys.executable)"
```

## Start Core Server

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
cp .env.example .env
make run
```

Or with Docker:

```bash
cp .env.example .env
make up
```

## Run Commands

Default (`LLM_BACKEND=auto`):

```bash
python examples/real-llm-smoke/smoke_flow.py
```

Force LiteLLM:

```bash
LLM_BACKEND=litellm python examples/real-llm-smoke/smoke_flow.py
```

Force Ollama:

```bash
LLM_BACKEND=ollama python examples/real-llm-smoke/smoke_flow.py
```

Force OpenAI (model is required):

```bash
OPENAI_API_KEY=*** OPENAI_MODEL=*** LLM_BACKEND=openai python examples/real-llm-smoke/smoke_flow.py
```

Use hybrid query endpoint explicitly:

```bash
USE_HYBRID=1 python examples/real-llm-smoke/smoke_flow.py
```

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `STATELOCK_BASE_URL` | `http://127.0.0.1:8000` | Core API base URL |
| `API_PREFIX` | `/memories` | Core memory prefix |
| `STATELOCK_API_KEY` | unset | Sends `X-Statelock-Api-Key` only when set |
| `STATELOCK_VERSION_HEADER` | unset | Sends `X-Statelock-Version` only when set (optional) |
| `STATELOCK_SESSION_ID` | `smoke:local:e2e` | Session scope for save/query |
| `STATELOCK_MEMORY_NAME` | `smoke_turn_1` | Memory `name` field |
| `STATELOCK_TAGS` | `smoke,llm,e2e` | Comma-separated tags |
| `TOP_K` | `3` | Query `top_k` |
| `USE_HYBRID` | `0` | `1` switches to `/query-hybrid` |
| `HYBRID_CANDIDATE_K` | `20` | Used only when `USE_HYBRID=1` |
| `HYBRID_SIMILARITY_WEIGHT` | `0.75` | Used only when `USE_HYBRID=1` |
| `HYBRID_RECENCY_WEIGHT` | `0.25` | Used only when `USE_HYBRID=1` |
| `LLM_BACKEND` | `auto` | `auto`, `litellm`, `ollama`, `openai` |
| `LLM_TIMEOUT_SECONDS` | `60` | Timeout for HTTP calls |
| `LITELLM_BASE_URL` | `http://127.0.0.1:4000` | LiteLLM base URL |
| `LITELLM_MODEL` | `chat_default` | LiteLLM model alias |
| `LITELLM_API_KEY` | unset | Bearer header sent only when set |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Ollama model |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base |
| `OPENAI_API_KEY` | unset | Required for OpenAI backend |
| `OPENAI_MODEL` | unset | Required when `OPENAI_API_KEY` is set |
| `TURN1_PROMPT` | built-in | First user prompt |
| `TURN2_PROMPT` | built-in | Follow-up user prompt |

## What the Script Calls

1. Preflight:
- `GET {STATELOCK_BASE_URL}/healthz`
- `GET {STATELOCK_BASE_URL}/readyz`
- fallback `GET {STATELOCK_BASE_URL}/` if needed.

2. Save:
- `POST {STATELOCK_BASE_URL}{API_PREFIX}/`
- payload: `{content, name, session_id, tags}`

3. Retrieve (default):
- `POST {STATELOCK_BASE_URL}{API_PREFIX}/query`
- payload: `{query_text, session_id, top_k}`

4. Retrieve (optional):
- `POST {STATELOCK_BASE_URL}{API_PREFIX}/query-hybrid` when `USE_HYBRID=1`

## Expected Output Shape

The script prints:
1. python diagnostics (`which python`, `python -V`, `sys.executable`),
2. resolved StateLock URL + API prefix,
3. preflight responses,
4. chosen backend + model for each LLM call,
5. full save response JSON,
6. full query response JSON,
7. assembled context text,
8. final summary JSON.

## Troubleshooting

1. `401 unauthorized` from Core:
- Set `STATELOCK_API_KEY` when Core has `AUTH_REQUIRED=true`.

2. Backend unavailable in auto mode:
- Start LiteLLM or Ollama, or provide OpenAI key+model.

3. OpenAI config error:
- If `OPENAI_API_KEY` is set, `OPENAI_MODEL` is required.

4. Parse mismatch:
- The script expects:
  - LiteLLM/OpenAI: `choices[0].message.content`
  - Ollama: `response`
- On mismatch it prints a short raw JSON preview for debugging.
