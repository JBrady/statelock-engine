from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from app.db.models import Span
from app.utils import cosine_similarity


@dataclass
class StubLLMBackend:
    vocab_size: int = 128
    proxy_kinds: tuple[str, ...] = ("lexical",)

    def available_proxy_kinds(self) -> list[str]:
        return list(self.proxy_kinds)

    def _seeded_vector(self, seed_text: str) -> list[float]:
        seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)
        return [rng.uniform(-1.0, 1.0) for _ in range(self.vocab_size)]

    def base_logits(self, query: str, target_thread_id: str) -> list[float]:
        return self._seeded_vector(f"base::{target_thread_id}::{query}")

    def span_vector(self, span: Span) -> list[float]:
        return self._seeded_vector(f"span::{span.span_id}::{span.thread_id}::{span.text}")

    def first_token_logits(self, query: str, target_thread_id: str, spans: list[Span]) -> list[float]:
        base = self.base_logits(query, target_thread_id)
        out = base[:]
        for span in spans:
            vec = self.span_vector(span)
            out = [a + b for a, b in zip(out, vec)]
        return out

    def proxy_score(self, span: Span, query: str, target_thread_id: str, kind: str) -> float:
        if kind == "gradients":
            vec = self.span_vector(span)
            return sum(abs(v) for v in vec) / len(vec)
        if kind == "attention":
            return cosine_similarity(query + " " + target_thread_id, span.text) * 0.9 + 0.05
        # lexical default
        return cosine_similarity(query + " " + target_thread_id, span.text) + 0.01
