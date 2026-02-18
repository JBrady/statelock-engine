"""Minimal memory + inference orchestration sample with fail-open memory."""

import requests

from app.services.automation_policy import build_confidence_signal, should_save_memory

STATELOCK = "http://127.0.0.1:8000"
LITELLM = "http://127.0.0.1:4000/v1/chat/completions"

session_id = "web:thread_42:user_7"
user_prompt = "Plan my weekend in Austin."

# 1) Retrieve memory context (fail-open if StateLock is unavailable)
memories = []
memory_warning = None
try:
    context_resp = requests.post(
        f"{STATELOCK}/memories/query-hybrid",
        json={
            "session_id": session_id,
            "query_text": user_prompt,
            "top_k": 5,
            "candidate_k": 20,
            "similarity_weight": 0.75,
            "recency_weight": 0.25,
        },
        timeout=10,
    )
    context_resp.raise_for_status()
    memories = context_resp.json().get("results", [])
except requests.RequestException as exc:
    memory_warning = f"memory query unavailable: {exc}"

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

# 3) Persist only if policy says this output is worth saving
confidence = build_confidence_signal(answer)
if should_save_memory(user_input=user_prompt, model_output=answer, always_save=False):
    try:
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
    except requests.RequestException as exc:
        memory_warning = f"memory save unavailable: {exc}"

print(answer)
print({"confidence_low": confidence["confidence_low"], "reason": confidence["reason"]})
if memory_warning:
    print({"warning": memory_warning})
