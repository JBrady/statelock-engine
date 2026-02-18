# OpenClaw Memory Automation Contract (v1)

This contract defines the default sidecar flow for local-first agents.

## Pre-model hook: `memory.query`

Request shape:

```json
{
  "query": "user prompt text",
  "session_id": "telegram:chat_123:user_9",
  "top_k": 5,
  "candidate_k": 20
}
```

Response shape:

```json
{
  "results": [
    {
      "content": "...",
      "session_id": "telegram:chat_123:user_9",
      "tags": ["policy"]
    }
  ]
}
```

Fail-open response shape (`failOpen=true`):

```json
{
  "results": [],
  "warning": "memory_unavailable",
  "details": "..."
}
```

## Post-model hook: `memory.save`

Request shape:

```json
{
  "content": "memory content to store",
  "name": "optional title",
  "tags": ["policy", "fallback"],
  "session_id": "telegram:chat_123:user_9",
  "model_output": "assistant answer text"
}
```

`model_output` is optional and used only to emit confidence signaling.

Response shape:

```json
{
  "id": "...",
  "content": "...",
  "session_id": "telegram:chat_123:user_9",
  "confidence_low": false,
  "confidence_reason": "none"
}
```

Fail-open response shape (`failOpen=true`):

```json
{
  "saved": false,
  "warning": "memory_unavailable",
  "details": "...",
  "confidence_low": true,
  "confidence_reason": "uncertainty_language"
}
```

## Session mapping strategy

Primary format:

`{channel}:{chat_or_thread}:{user_or_agent}`

Fallback:

`agent:chat:main`

## Save policy defaults

- `always_save=false`
- save when content includes trigger classes: `decision`, `preference`, `todo`, `policy`
- save on explicit `/memory_save` command

Cloud escalation remains in agent/router layer; `confidence_low` is only a hint signal.
