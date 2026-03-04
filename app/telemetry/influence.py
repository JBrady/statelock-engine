from __future__ import annotations

from app.backends.stub_llm import StubLLMBackend
from app.db.models import Span
from app.telemetry.metrics import normalize_scores

PROXY_FALLBACK_ORDER = ["gradients", "attention", "lexical"]


def choose_proxy_kind(backend: StubLLMBackend) -> str:
    available = set(backend.available_proxy_kinds())
    for kind in PROXY_FALLBACK_ORDER:
        if kind in available:
            return kind
    return "lexical"


def proxy_influence(
    backend: StubLLMBackend,
    spans: list[Span],
    query: str,
    target_thread_id: str,
) -> tuple[str, list[dict]]:
    kind = choose_proxy_kind(backend)
    rows = []
    for span in spans:
        raw = backend.proxy_score(span, query=query, target_thread_id=target_thread_id, kind=kind)
        rows.append(
            {
                "span_id": span.span_id,
                "thread_id": span.thread_id,
                "raw_score": float(raw),
                "w": 0.0,
            }
        )
    return kind, normalize_scores(rows)
