# OpenClaw Tooling Example

This example shows minimal sidecar calls OpenClaw tools/hooks can make to StateLock.

Tool surface:

- `memory.save`
- `memory.query`
- `memory.clear_session`
- pre-model `memory.query` hook request contract
- post-model `memory.save` hook request contract + `confidence_low` signal

If you expose these through Telegram in OpenClaw, a practical mapping is:

- `memory.save` -> `/memory_save`
- `memory.query` -> `/memory_query`

Recommended session format:

`{channel}:{thread_or_chat}:{user_or_agent}`

Use `example_tool_calls.json` as a template for your own tool adapter.
Automation flow contract:

- `AUTOMATION_CONTRACT.md`

For a portable, versioned OpenClaw runtime bundle (plugin + skills + config snippet), see:

- `openclaw-runtime/README.md`

URL note:

- If OpenClaw runs in Docker, use `http://host.docker.internal:8000`.
- If OpenClaw runs directly on host, use `http://127.0.0.1:8000`.
