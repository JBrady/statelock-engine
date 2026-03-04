from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backends.stub_llm import StubLLMBackend
from app.db.models import Span, Turn
from app.telemetry.metrics import normalize_scores
from app.utils import cosine_similarity, kl_divergence, softmax


def build_candidate_set(
    db: Session,
    conversation_id: str,
    selected_spans: list[Span],
    proxy_rows: list[dict],
    query: str,
    max_total: int,
) -> list[Span]:
    span_by_id = {s.span_id: s for s in selected_spans}

    relevance_sorted = sorted(
        selected_spans,
        key=lambda s: cosine_similarity(query, s.text),
        reverse=True,
    )
    top_relevance = relevance_sorted[:6]

    proxy_sorted = sorted(proxy_rows, key=lambda r: r["raw_score"], reverse=True)
    top_proxy = [span_by_id[r["span_id"]] for r in proxy_sorted if r["span_id"] in span_by_id][:6]

    newest_user_span = None
    newest_user_turn = db.scalar(
        select(Turn)
        .where(Turn.conversation_id == conversation_id, Turn.speaker == "user")
        .order_by(Turn.created_at.desc())
    )
    if newest_user_turn:
        newest_user_span = next(
            (s for s in selected_spans if newest_user_turn.turn_id in (s.source_turn_ids_json or [])),
            None,
        )

    newest_tool_span = None
    newest_tool_turn = db.scalar(
        select(Turn)
        .where(Turn.conversation_id == conversation_id, Turn.speaker == "tool")
        .order_by(Turn.created_at.desc())
    )
    if newest_tool_turn:
        newest_tool_span = next(
            (s for s in selected_spans if newest_tool_turn.turn_id in (s.source_turn_ids_json or [])),
            None,
        )

    required = [s for s in [newest_user_span, newest_tool_span] if s is not None]

    ordered: list[Span] = []
    seen = set()

    for span in required + top_relevance + top_proxy:
        if span.span_id not in seen:
            seen.add(span.span_id)
            ordered.append(span)

    if len(ordered) <= max_total:
        return ordered

    required_ids = {s.span_id for s in required}
    required_kept = [s for s in ordered if s.span_id in required_ids]

    proxy_rank = {row["span_id"]: idx for idx, row in enumerate(proxy_sorted)}
    rest = [s for s in ordered if s.span_id not in required_ids]
    rest.sort(key=lambda s: proxy_rank.get(s.span_id, 10_000))

    kept = required_kept + rest
    return kept[:max_total]


def ablation_kl_influence(
    backend: StubLLMBackend,
    query: str,
    target_thread_id: str,
    baseline_spans: list[Span],
    candidate_spans: list[Span],
) -> list[dict]:
    baseline_logits = backend.first_token_logits(query, target_thread_id, baseline_spans)
    p = softmax(baseline_logits)

    rows: list[dict] = []
    baseline_ids = {s.span_id for s in baseline_spans}
    for span in candidate_spans:
        if span.span_id not in baseline_ids:
            continue
        without = [s for s in baseline_spans if s.span_id != span.span_id]
        q_logits = backend.first_token_logits(query, target_thread_id, without)
        q = softmax(q_logits)
        influence = kl_divergence(p, q, eps=1e-12)
        rows.append(
            {
                "span_id": span.span_id,
                "thread_id": span.thread_id,
                "raw_score": influence,
                "w": 0.0,
            }
        )

    return normalize_scores(rows)
