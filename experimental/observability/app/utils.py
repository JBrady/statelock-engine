from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_text(text).lower())


def token_count_est(text: str) -> int:
    return len(tokenize(text))


def cosine_similarity(a_text: str, b_text: str) -> float:
    a_tokens = tokenize(a_text)
    b_tokens = tokenize(b_text)
    if not a_tokens or not b_tokens:
        return 0.0

    a_counts = Counter(a_tokens)
    b_counts = Counter(b_tokens)
    dot = sum(a_counts[t] * b_counts[t] for t in (set(a_counts) & set(b_counts)))
    a_norm = math.sqrt(sum(v * v for v in a_counts.values()))
    b_norm = math.sqrt(sum(v * v for v in b_counts.values()))
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(dot / (a_norm * b_norm))


def softmax(logits: list[float]) -> list[float]:
    if not logits:
        return []
    max_logit = max(logits)
    exps = [math.exp(x - max_logit) for x in logits]
    total = sum(exps)
    return [x / total for x in exps]


def kl_divergence(p: list[float], q: list[float], eps: float = 1e-12) -> float:
    return float(sum(pi * math.log((pi + eps) / (qi + eps)) for pi, qi in zip(p, q)))
