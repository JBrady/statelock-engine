# Agent Memory Loop (Core Track)

This example demonstrates a simple interactive agent loop that uses StateLock Core as a memory sidecar:

1. user enters a prompt,
2. agent extracts fact-shaped memories from the user message (`my name is ...`, `call me ...`, `I prefer ...`) and saves them when enabled,
3. agent retrieves related memories from StateLock,
4. agent assembles a memory context block,
5. agent calls an LLM,
6. agent optionally saves the assistant response,
7. repeat.

## Scope Guardrails

- Core Track only (`/memories/*` endpoints).
- No observability integration.
- Python stdlib only.
- No new dependencies.

## Setup / Preflight

Start StateLock Core first (from repo root):

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
cp .env.example .env
make run
```

Or Docker:

```bash
cp .env.example .env
make up
```

The script preflight checks:

- `GET /healthz`
- `GET /readyz`
- fallback `GET /` with explanation if health/ready are not successful.

## Python Environment Sanity

```bash
which python
python -V
which python3
python3 -V
python3 -c "import sys; print(sys.executable)"
```

## Run

```bash
python3 examples/agent-memory-loop/agent_loop.py
```

Type `exit` or `quit` to stop the loop.

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `STATELOCK_BASE_URL` | `http://127.0.0.1:8000` | Core API base URL |
| `API_PREFIX` | `/memories` | Core memory prefix |
| `STATELOCK_API_KEY` | unset | Sends `X-Statelock-Api-Key` only when set |
| `STATELOCK_VERSION_HEADER` | unset | Sends `X-Statelock-Version` only when set |
| `STATELOCK_SESSION_ID` | `agent:chat:main` | Session scope for reads/writes |
| `TOP_K` | `5` | Retrieval `top_k` |
| `USE_HYBRID` | `0` | `1` uses `/query-hybrid`, else `/query` |
| `HYBRID_CANDIDATE_K` | `20` | Used when `USE_HYBRID=1` |
| `HYBRID_SIMILARITY_WEIGHT` | `0.75` | Used when `USE_HYBRID=1` |
| `HYBRID_RECENCY_WEIGHT` | `0.25` | Used when `USE_HYBRID=1` |
| `LLM_BACKEND` | `auto` | `auto`, `litellm`, `ollama`, `openai` |
| `LLM_TIMEOUT_SECONDS` | `60` | HTTP timeout |
| `LITELLM_BASE_URL` | `http://127.0.0.1:4000` | LiteLLM endpoint |
| `LITELLM_MODEL` | `chat_default` | LiteLLM model alias |
| `LITELLM_API_KEY` | unset | Bearer header only when set |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Ollama model |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base |
| `OPENAI_API_KEY` | unset | Required for OpenAI backend |
| `OPENAI_MODEL` | unset | Required if OpenAI is used |
| `STATELOCK_TAGS` | `agent-loop,memory` | Base tags for saved memories |
| `SAVE_MODE` | `always` | `always`, `never`, `keyword` |
| `SAVE_KEYWORDS` | `decision,preference,todo,policy` | Used when `SAVE_MODE=keyword` |
| `FACT_SAVE` | `1` | Enables extracted fact saves from user text |

## Save Policy Modes

1. `always` (default): save every assistant response.
2. `never`: disable assistant-response memory writes.
3. `keyword`: save assistant responses only if any keyword appears in user/assistant text.

`SAVE_MODE` applies to assistant-response saves only. Fact extraction saves are controlled by `FACT_SAVE`.

## Fact Extraction Rules

When `FACT_SAVE=1` (default), user text is scanned for:

1. `my name is X` -> memory content `User name is X`
2. `call me X` -> memory content `User name is X`
3. `I prefer X` -> memory content `User prefers X`

Extracted memories are written as separate records with additional tags such as `fact`, `name`, and `preference`.

## Example Interactive Transcript

```text
== Resolved Config ==
STATELOCK_BASE_URL: http://127.0.0.1:8000
API_PREFIX: /memories
STATELOCK_SESSION_ID: agent:chat:main
TOP_K: 5
LLM_BACKEND: auto
SAVE_MODE: always

You> summarize what we decided about cloud fallback
[memories] retrieved: 2
[llm] backend=litellm model=chat_default
Assistant> We agreed to stay local-first and escalate for low confidence or correctness-critical work.
[memory-save] triggered=true reason=always
[memory-save] full response:
{ ... }
[memory-save] identifier=...

You> my name is John and I prefer dark mode
[fact-save] extracted=2
[memories] retrieved: 3
[llm] backend=litellm model=chat_default
Assistant> Got it, John. I'll keep dark mode as your preference.
[memory-save] triggered=true reason=always

You> quit
Exiting agent loop.
```

## Troubleshooting

1. `401` from Core:
- set `STATELOCK_API_KEY` if Core has `AUTH_REQUIRED=true`.

2. Backend unavailable:
- ensure LiteLLM and/or Ollama are running, or configure OpenAI key+model.

3. OpenAI config:
- if `LLM_BACKEND=openai`, both `OPENAI_API_KEY` and `OPENAI_MODEL` are required.

4. Parse mismatch:
- expected response shapes:
  - LiteLLM/OpenAI: `choices[0].message.content`
  - Ollama: `response`
- script prints a short raw JSON preview when parse fails.
