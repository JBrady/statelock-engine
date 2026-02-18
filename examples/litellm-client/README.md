# LiteLLM Client Flow Example

This folder documents an app-side orchestration pattern:

1. Retrieve context from StateLock (`/memories/query-hybrid`)
2. Call LiteLLM alias (for example `chat_default`)
3. Save memory candidates back to StateLock (`/memories/upsert`)

StateLock remains the memory sidecar; LiteLLM remains the model router.
