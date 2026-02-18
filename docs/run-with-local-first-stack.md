# Run StateLock With a Local-First AI Stack

This setup keeps concerns separate:

- **Ollama**: local model runtime
- **LiteLLM**: model routing/fallback
- **OpenClaw**: agent runtime + tools
- **StateLock Engine**: memory sidecar API

StateLock does not route models in this architecture.

## 1) Start StateLock

```bash
cp .env.example .env
make up
```

API docs:

- `http://127.0.0.1:8000/docs`

## 2) Keep your existing LiteLLM aliases

Example aliases expected in your local-first stack:

- `chat_default`
- `deep_default`
- `code_default`
- `cloud_reason`
- `cloud_code`

StateLock does not need these model aliases directly; it stores/retrieves memory for agents that use them.

## 3) OpenClaw tool integration (sidecar mode)

Use a tool wrapper that calls StateLock:

- `memory.save`
- `memory.query`
- `memory.clear_session`

In the current OpenClaw Telegram setup, these are exposed as slash commands:

- `/memory_save ...`
- `/memory_query ...`

Portable runtime bundle (plugin + skills + config snippet):

- `examples/openclaw-tooling/openclaw-runtime/`

Connection URL:

- OpenClaw in Docker: `http://host.docker.internal:8000`
- OpenClaw on host: `http://127.0.0.1:8000`

Recommended `session_id` format:

`{channel}:{thread_or_chat}:{user_or_agent}`

Example:

`telegram:chat_12345:user_987`

## 4) Example flow

1. Agent receives message.
2. Derive session id: `{channel}:{thread_or_chat}:{user_or_agent}`.
3. Call `memory.query` for session context.
3. Build prompt with retrieved memories.
4. Call LiteLLM model alias.
5. Emit confidence hint (`confidence_low`) from model output.
6. Save durable facts with `memory.save` based on policy triggers.

Automation contract:

- `examples/openclaw-tooling/AUTOMATION_CONTRACT.md`

## 5) Smoke checks

```bash
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/memories/?limit=1
curl -s http://127.0.0.1:8000/healthz
curl -s http://127.0.0.1:8000/readyz
```

## 6) Save a test memory (for `/memory_query`)

Your OpenClaw `memory_query` tool currently queries this session id:

- `agent:chat:main`

Save a test memory into that same session:

```bash
curl -sS -X POST http://127.0.0.1:8000/memories/ \
  -H "content-type: application/json" \
  -H "X-Statelock-Version: 1" \
  -d '{
    "content": "We use local models first and escalate to cloud when confidence is low or correctness is critical.",
    "name": "cloud fallback policy",
    "session_id": "agent:chat:main",
    "tags": ["policy", "fallback"]
  }'
```

Optional: list memories in that session to confirm it was saved:

```bash
curl -sS "http://127.0.0.1:8000/memories/?session_id=agent:chat:main&limit=10&offset=0"
```

Optional: direct API query check (without OpenClaw):

```bash
curl -sS -X POST http://127.0.0.1:8000/memories/query-hybrid \
  -H "content-type: application/json" \
  -H "X-Statelock-Version: 1" \
  -d '{
    "query_text": "what did we decide about cloud fallback",
    "session_id": "agent:chat:main",
    "top_k": 5,
    "candidate_k": 20,
    "similarity_weight": 0.75,
    "recency_weight": 0.25
  }'
```

Then test in Telegram:

- `/memory_query what did we decide about cloud fallback`

## 7) Save/query directly from Telegram

If your OpenClaw sidecar tooling is configured, you can do both steps from Telegram:

- Save:
  - `/memory_save We use local first and only escalate to cloud when confidence is low.`
- Save with metadata (JSON):
  - `/memory_save {"content":"Cloud fallback: low confidence or correctness-critical tasks.","name":"fallback policy","tags":["policy","fallback"]}`
  - Telegram-safe variant (no brackets): `/memory_save {"content":"Cloud fallback: low confidence or correctness-critical tasks.","name":"fallback policy","tags":"policy,fallback"}`
- Query:
  - `/memory_query cloud fallback`

Expected query response shape:

```json
{"results":[...]}
```

If `failOpen=true` in the OpenClaw plugin config and StateLock is unavailable, query/save tools return warning JSON and agent chat can continue.
