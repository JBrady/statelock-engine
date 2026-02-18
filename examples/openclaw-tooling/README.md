# OpenClaw Tooling Example

This example shows minimal sidecar calls OpenClaw tools/hooks can make to StateLock.

Tool surface:

- `memory.save`
- `memory.query`
- `memory.clear_session`

Recommended session format:

`{channel}:{thread_or_chat}:{user_or_agent}`

Use `example_tool_calls.json` as a template for your own tool adapter.
