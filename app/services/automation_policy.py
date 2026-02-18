import re
from typing import Dict, Optional

LOW_CONFIDENCE_PATTERNS = [
    re.compile(r"\b(i\s+am\s+not\s+sure|i\s+think|maybe|might|uncertain)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+confident\b", re.IGNORECASE),
]

SAVE_TRIGGER_PATTERNS = [
    re.compile(r"\bdecision\b", re.IGNORECASE),
    re.compile(r"\bpreference\b", re.IGNORECASE),
    re.compile(r"\btodo\b", re.IGNORECASE),
    re.compile(r"\bpolicy\b", re.IGNORECASE),
]


def derive_session_id(
    channel: str,
    chat_or_thread: Optional[str],
    user_or_agent: Optional[str],
    fallback: str = "agent:chat:main",
) -> str:
    c = (channel or "").strip()
    t = (chat_or_thread or "").strip()
    u = (user_or_agent or "").strip()
    if c and t and u:
        return f"{c}:{t}:{u}"
    return fallback


def should_save_memory(
    user_input: str,
    model_output: str,
    always_save: bool = False,
    explicit_memory_command: bool = False,
) -> bool:
    if always_save or explicit_memory_command:
        return True

    text = f"{user_input}\n{model_output}".strip()
    if not text:
        return False

    return any(pattern.search(text) for pattern in SAVE_TRIGGER_PATTERNS)


def build_confidence_signal(model_output: str) -> Dict[str, object]:
    output = (model_output or "").strip()
    if not output:
        return {"confidence_low": True, "reason": "empty_response"}

    for pattern in LOW_CONFIDENCE_PATTERNS:
        if pattern.search(output):
            return {"confidence_low": True, "reason": "uncertainty_language"}

    if len(output.split()) < 8:
        return {"confidence_low": True, "reason": "too_short"}

    return {"confidence_low": False, "reason": "none"}
