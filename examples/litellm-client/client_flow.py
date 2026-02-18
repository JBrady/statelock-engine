"""
Minimal memory + inference orchestration sample.
"""

import requests

STATELOCK = "http://127.0.0.1:8000"
LITELLM = "http://127.0.0.1:4000/v1/chat/completions"

session_id = "web:thread_42:user_7"
user_prompt = "Plan my weekend in Austin."

# 1) Retrieve memory context
context_resp = requests.post(
    f"{STATELOCK}/memories/query-hybrid",
    json={
        "session_id": session_id,
        "query_text": user_prompt,
        "top_k": 5,
    },
    timeout=10,
)
context_resp.raise_for_status()
memories = context_resp.json().get("results", [])
context_text = (
    "\n".join([f"- {m['content']}" for m in memories])
    if memories
    else "No prior memory."
)

# 2) Call LiteLLM alias
messages = [
    {"role": "system", "content": "Use prior memory context when relevant."},
    {"role": "system", "content": f"Memory:\n{context_text}"},
    {"role": "user", "content": user_prompt},
]
model_resp = requests.post(
    LITELLM,
    json={"model": "chat_default", "messages": messages, "max_tokens": 500},
    headers={"Authorization": "Bearer dummy"},
    timeout=30,
)
model_resp.raise_for_status()
answer = model_resp.json()["choices"][0]["message"]["content"]

# 3) Persist useful memory
requests.post(
    f"{STATELOCK}/memories/upsert",
    json={
        "external_id": "last_weekend_plan",
        "session_id": session_id,
        "name": "Recent recommendation",
        "content": answer,
        "tags": ["recommendation"],
    },
    timeout=10,
).raise_for_status()

print(answer)
