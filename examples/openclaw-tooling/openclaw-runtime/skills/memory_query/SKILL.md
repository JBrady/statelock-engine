---
name: memory_query
description: Query StateLock memory sidecar and return matching memories.
user-invocable: true
command-dispatch: tool
command-tool: memory_query_tool
---

# Memory Query

Use this skill when the user asks to query memory or runs `/memory_query`.

## Behavior

1. Read the command text after `/memory_query` as the query text.
2. Query StateLock and return only the JSON payload.

## Notes

- Do not invent or summarize memory results.
