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

Recommended `session_id` format:

`{channel}:{thread_or_chat}:{user_or_agent}`

Example:

`telegram:chat_12345:user_987`

## 4) Example flow

1. Agent receives message.
2. Call `memory.query` for session context.
3. Build prompt with retrieved memories.
4. Call LiteLLM model alias.
5. Save durable facts with `memory.save`.

## 5) Smoke checks

```bash
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/memories/?limit=1
```
