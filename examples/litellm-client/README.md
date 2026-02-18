# LiteLLM Client Flow Example

This folder documents an app-side orchestration pattern:

1. Retrieve context from StateLock (`/memories/query-hybrid`)
2. Call LiteLLM alias (for example `chat_default`)
3. Generate `confidence_low` hint from model output
4. Save memory candidates back to StateLock (`/memories/upsert`) only when policy says to save
5. Fail open if StateLock is unavailable (chat still proceeds)

StateLock remains the memory sidecar; LiteLLM remains the model router.
