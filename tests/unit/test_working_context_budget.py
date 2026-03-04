from __future__ import annotations

from datetime import datetime, timedelta

from app.context_builder.builder import build_working_context
from app.db.models import Conversation, Span, Thread, Turn
from app.db.session import SessionLocal


def test_working_context_small_budget_pruning_order():
    db = SessionLocal()
    c = Conversation(title="budget", max_context_tokens=120)
    db.add(c)
    db.flush()

    t = Thread(
        conversation_id=c.conversation_id,
        thread_id="networking",
        name="networking",
        summary="networking diagnostics",
    )
    db.add(t)
    db.flush()

    now = datetime.utcnow()
    low_trust = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="network issue packet packet packet packet packet packet packet packet",
        token_count_est=20,
        thread_id="networking",
        span_type="dialog",
        trust_score=0.1,
        trust_reason="low",
        first_seen_at=now - timedelta(hours=3),
    )
    old_unused = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="networking baseline old data old data old data old data",
        token_count_est=20,
        thread_id="networking",
        span_type="dialog",
        trust_score=0.9,
        trust_reason="ok",
        first_seen_at=now - timedelta(hours=5),
    )
    low_relevance = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="gardening roses soil pruning fertilizer sunlight",
        token_count_est=20,
        thread_id="networking",
        span_type="dialog",
        trust_score=0.95,
        trust_reason="ok",
        first_seen_at=now - timedelta(hours=1),
    )
    tool_long = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text=" ".join(["trace"] * 260),
        token_count_est=260,
        thread_id="networking",
        span_type="tool_output",
        trust_score=0.95,
        trust_reason="ok",
        first_seen_at=now - timedelta(minutes=20),
    )
    db.add_all([low_trust, old_unused, low_relevance, tool_long])
    db.flush()

    wc = build_working_context(db, c, query="network troubleshooting trace packet loss", max_context_tokens=120)
    drop_order = [d["reason"] for d in wc.selection_log_json["drop_order"]]

    assert "trim_recent_turns" in drop_order
    assert "compress_long_tool_outputs" in drop_order
    assert "drop_low_trust" in drop_order
    assert "drop_old_unused" in drop_order
    assert "drop_low_relevance" in drop_order

    rank = {
        "trim_recent_turns": 0,
        "compress_long_tool_outputs": 1,
        "drop_low_trust": 2,
        "drop_old_unused": 3,
        "drop_low_relevance": 4,
        "fallback_keep_best_span": 5,
    }
    last = -1
    for reason in drop_order:
        current = rank[reason]
        assert current >= last
        last = current

    assert wc.token_count_est <= 120
    db.close()


def test_recent_turns_trim_happens_before_evidence_drops():
    db = SessionLocal()
    c = Conversation(title="recent-first", max_context_tokens=80)
    db.add(c)
    db.flush()

    db.add(Thread(conversation_id=c.conversation_id, thread_id="networking", name="networking", summary="networking"))
    db.flush()

    for i in range(8):
        db.add(
            Turn(
                conversation_id=c.conversation_id,
                speaker="user" if i % 2 == 0 else "assistant",
                text=f"Turn {i} with verbose conversational content about setup and context details.",
            )
        )

    for i in range(4):
        db.add(
            Span(
                conversation_id=c.conversation_id,
                source_turn_ids_json=[],
                text=f"network diagnostic evidence span {i}",
                token_count_est=10,
                thread_id="networking",
                span_type="dialog",
                trust_score=0.9,
                trust_reason="ok",
            )
        )
    db.flush()

    wc = build_working_context(db, c, query="unrelated low overlap query", max_context_tokens=80)
    drop_order = wc.selection_log_json["drop_order"]
    reasons = [d["reason"] for d in drop_order]
    assert "trim_recent_turns" in reasons

    first_evidence_drop_idx = None
    for idx, reason in enumerate(reasons):
        if reason in {"drop_low_trust", "drop_old_unused", "drop_low_relevance"}:
            first_evidence_drop_idx = idx
            break
    if first_evidence_drop_idx is not None:
        assert reasons.index("trim_recent_turns") < first_evidence_drop_idx

    db.close()


def test_scores_only_include_considered_candidate_set():
    db = SessionLocal()
    c = Conversation(title="scores-candidates")
    db.add(c)
    db.flush()
    db.add(Thread(conversation_id=c.conversation_id, thread_id="networking", name="networking", summary="networking"))
    db.flush()

    now = datetime.utcnow()
    s1 = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="network packet diagnostics",
        token_count_est=4,
        thread_id="networking",
        span_type="dialog",
        trust_score=0.9,
        trust_reason="ok",
        first_seen_at=now - timedelta(minutes=15),
    )
    s2 = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="router baseline checks",
        token_count_est=4,
        thread_id="networking",
        span_type="dialog",
        trust_score=0.9,
        trust_reason="ok",
        first_seen_at=now - timedelta(minutes=10),
    )
    s3 = Span(
        conversation_id=c.conversation_id,
        source_turn_ids_json=[],
        text="cosmology unrelated",
        token_count_est=3,
        thread_id="cosmology",
        span_type="dialog",
        trust_score=0.9,
        trust_reason="ok",
        first_seen_at=now - timedelta(minutes=5),
    )
    db.add_all([s1, s2, s3])
    db.flush()

    wc = build_working_context(db, c, query="network packet loss", max_context_tokens=500)
    selection_log = wc.selection_log_json

    before = set(selection_log["selected_before_budget"])
    score_keys = set(selection_log["scores"].keys())
    assert score_keys == before
    db.close()


def test_fallback_keep_best_span_when_pruning_would_empty_evidence():
    db = SessionLocal()
    c = Conversation(title="fallback-empty", max_context_tokens=60)
    db.add(c)
    db.flush()
    db.add(Thread(conversation_id=c.conversation_id, thread_id="networking", name="networking", summary="networking"))
    db.flush()

    for i in range(4):
        db.add(
            Turn(
                conversation_id=c.conversation_id,
                speaker="user" if i % 2 == 0 else "assistant",
                text=f"long recent turn content {i} " + ("word " * 40),
            )
        )

    now = datetime.utcnow()
    spans = []
    for i in range(3):
        spans.append(
            Span(
                conversation_id=c.conversation_id,
                source_turn_ids_json=[],
                text=f"evidence span {i} " + ("data " * 80),
                token_count_est=85,
                thread_id="networking",
                span_type="dialog",
                trust_score=0.1 if i == 0 else 0.8,
                trust_reason="test",
                first_seen_at=now - timedelta(hours=3 + i),
            )
        )
    db.add_all(spans)
    db.flush()

    wc = build_working_context(db, c, query="mismatched query tokens", max_context_tokens=60)
    reasons = [d["reason"] for d in wc.selection_log_json["drop_order"]]

    assert wc.selection_log_json["selected_before_budget"]
    assert wc.selection_log_json["selected_after_budget"]
    assert len(wc.selected_span_ids_json) >= 1
    assert "fallback_keep_best_span" in reasons
    db.close()
