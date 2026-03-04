from __future__ import annotations

from datetime import datetime, timedelta

from app.backends.stub_llm import StubLLMBackend
from app.db.models import Conversation, Span, Turn
from app.db.session import SessionLocal
from app.telemetry.ablation import ablation_kl_influence, build_candidate_set
from app.utils import kl_divergence, softmax


def _seed_for_candidate_set():
    db = SessionLocal()
    c = Conversation(title="ablation")
    db.add(c)
    db.flush()

    turns = [
        Turn(conversation_id=c.conversation_id, speaker="user", text="u1"),
        Turn(conversation_id=c.conversation_id, speaker="assistant", text="a1"),
        Turn(conversation_id=c.conversation_id, speaker="tool", text="t1"),
        Turn(conversation_id=c.conversation_id, speaker="user", text="u2"),
    ]
    db.add_all(turns)
    db.flush()

    spans = []
    for idx in range(14):
        source_turn = turns[idx % len(turns)]
        spans.append(
            Span(
                conversation_id=c.conversation_id,
                created_at=datetime.utcnow() - timedelta(minutes=idx),
                source_turn_ids_json=[source_turn.turn_id],
                text=f"span {idx} networking relevance {idx}",
                token_count_est=10,
                thread_id="networking" if idx % 2 == 0 else "cosmology",
                span_type="dialog",
                trust_score=0.9,
                trust_reason="test",
            )
        )
    db.add_all(spans)
    db.flush()

    proxy_rows = [
        {"span_id": s.span_id, "thread_id": s.thread_id, "raw_score": float(20 - i), "w": 0.0}
        for i, s in enumerate(spans)
    ]
    db.commit()
    return db, c, spans, proxy_rows, turns


def test_candidate_set_recipe_and_cap():
    db, c, spans, proxy_rows, turns = _seed_for_candidate_set()
    try:
        candidates = build_candidate_set(
            db,
            conversation_id=c.conversation_id,
            selected_spans=spans,
            proxy_rows=proxy_rows,
            query="networking help",
            max_total=12,
        )
        assert len(candidates) <= 12

        newest_user_turn = turns[-1]
        newest_user_span = next(s for s in spans if newest_user_turn.turn_id in (s.source_turn_ids_json or []))
        newest_tool_turn = next(t for t in reversed(turns) if t.speaker == "tool")
        newest_tool_span = next(s for s in spans if newest_tool_turn.turn_id in (s.source_turn_ids_json or []))

        ids = {s.span_id for s in candidates}
        assert newest_user_span.span_id in ids
        assert newest_tool_span.span_id in ids
    finally:
        db.close()


def test_ablation_kl_first_token_softmax():
    db = SessionLocal()
    c = Conversation(title="kl")
    db.add(c)
    db.flush()

    spans = [
        Span(
            conversation_id=c.conversation_id,
            source_turn_ids_json=[],
            text="network packet trace",
            token_count_est=5,
            thread_id="networking",
            span_type="dialog",
            trust_score=0.9,
            trust_reason="test",
        ),
        Span(
            conversation_id=c.conversation_id,
            source_turn_ids_json=[],
            text="router dns reset",
            token_count_est=5,
            thread_id="networking",
            span_type="dialog",
            trust_score=0.9,
            trust_reason="test",
        ),
    ]
    db.add_all(spans)
    db.flush()

    backend = StubLLMBackend(vocab_size=32)
    rows = ablation_kl_influence(
        backend,
        query="network troubleshooting",
        target_thread_id="networking",
        baseline_spans=spans,
        candidate_spans=spans,
    )

    baseline = softmax(backend.first_token_logits("network troubleshooting", "networking", spans))
    without0 = softmax(backend.first_token_logits("network troubleshooting", "networking", [spans[1]]))
    expected0 = kl_divergence(baseline, without0)

    by_id = {r["span_id"]: r for r in rows}
    assert spans[0].span_id in by_id
    assert by_id[spans[0].span_id]["raw_score"] > 0
    assert abs(by_id[spans[0].span_id]["raw_score"] - expected0) < 1e-9
    db.close()
