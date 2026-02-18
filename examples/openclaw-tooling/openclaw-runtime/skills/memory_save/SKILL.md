---
name: memory_save
description: Save a memory entry to the StateLock sidecar.
user-invocable: true
command-dispatch: tool
command-tool: memory_save_tool
---

# Memory Save

Use this skill when the user asks to store memory or runs `/memory_save`.

## Behavior

1. Read the command text after `/memory_save` as the memory content.
2. Save it to StateLock.
3. Return only the JSON payload.

## Notes

- Do not summarize or rewrite the saved memory.
- Accept either:
  - plain text after `/memory_save`
  - JSON object with `content`, optional `name`, optional `tags`, optional `session_id`
