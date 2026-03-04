from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Span, Thread, Turn
from app.services.pipeline_log import log_pipeline
from app.utils import cosine_similarity, token_count_est, tokenize

SPAN_TOKENS_TARGET = 80
SPAN_OVERLAP_TOKENS = 20
MIN_SPAN_TOKENS = 30
ASSIGN_THRESHOLD = 0.42
NEW_THREAD_THRESHOLD = 0.28


def _thread_records(db: Session, conversation_id: str) -> list[Thread]:
    return list(db.scalars(select(Thread).where(Thread.conversation_id == conversation_id)).all())


def _create_thread(db: Session, conversation_id: str, thread_id: str, summary_seed: str) -> Thread:
    now = datetime.utcnow()
    thread = Thread(
        conversation_id=conversation_id,
        thread_id=thread_id,
        name=thread_id,
        summary=summary_seed[:400],
        created_at=now,
        updated_at=now,
        last_activity_at=now,
        span_count=0,
    )
    db.add(thread)
    db.flush()
    return thread


def _generate_thread_id(threads: list[Thread]) -> str:
    existing = {t.thread_id for t in threads}
    n = 1
    while f"thread-{n}" in existing:
        n += 1
    return f"thread-{n}"


def _assign_thread(db: Session, conversation_id: str, span_text: str, explicit_hint: str | None) -> tuple[str, dict]:
    threads = _thread_records(db, conversation_id)
    if explicit_hint:
        if not any(t.thread_id == explicit_hint for t in threads):
            _create_thread(db, conversation_id, explicit_hint, span_text)
        return explicit_hint, {"rule": "explicit_user_tags", "score": 1.0}

    if not threads:
        new_id = "thread-1"
        _create_thread(db, conversation_id, new_id, span_text)
        return new_id, {"rule": "fallback_new_thread_if_empty", "score": 0.0}

    scored = [(t, cosine_similarity(span_text, t.summary)) for t in threads]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_thread, top_score = scored[0]

    if top_score >= ASSIGN_THRESHOLD:
        return top_thread.thread_id, {"rule": "similarity_to_thread_summaries", "score": top_score}

    if top_score < NEW_THREAD_THRESHOLD:
        new_id = _generate_thread_id(threads)
        _create_thread(db, conversation_id, new_id, span_text)
        return new_id, {"rule": "fallback_new_thread_if_low_similarity", "score": top_score}

    # in-between threshold uses latest updated thread for determinism
    threads.sort(key=lambda t: t.updated_at, reverse=True)
    chosen = threads[0]
    return chosen.thread_id, {"rule": "fallback_recent_thread", "score": top_score}


def _chunk_turn(turn: Turn, target: int = SPAN_TOKENS_TARGET, overlap: int = SPAN_OVERLAP_TOKENS) -> list[tuple[str, int]]:
    tokens = tokenize(turn.text)
    if not tokens:
        return []

    if len(tokens) <= target:
        text = " ".join(tokens)
        return [(text, len(tokens))]

    chunks: list[tuple[str, int]] = []
    stride = max(1, target - overlap)
    for start in range(0, len(tokens), stride):
        window = tokens[start : start + target]
        if len(window) < MIN_SPAN_TOKENS and chunks:
            break
        if len(window) < MIN_SPAN_TOKENS:
            continue
        chunks.append((" ".join(window), len(window)))
        if start + target >= len(tokens):
            break
    return chunks


def _refresh_thread_stats(db: Session, conversation_id: str) -> None:
    threads = _thread_records(db, conversation_id)
    spans = list(db.scalars(select(Span).where(Span.conversation_id == conversation_id)).all())
    by_thread: dict[str, list[Span]] = defaultdict(list)
    for span in spans:
        by_thread[span.thread_id].append(span)

    for thread in threads:
        thread_spans = by_thread.get(thread.thread_id, [])
        thread.span_count = len(thread_spans)
        if thread_spans:
            latest = max(thread_spans, key=lambda s: s.created_at)
            thread.last_activity_at = latest.created_at
            joined = " ".join(s.text for s in sorted(thread_spans, key=lambda s: s.created_at)[-5:])
            thread.summary = joined[:600]
            thread.updated_at = datetime.utcnow()
    db.flush()


def segment_conversation(db: Session, conversation_id: str, mode: str = "incremental") -> int:
    turns = list(
        db.scalars(
            select(Turn)
            .where(Turn.conversation_id == conversation_id)
            .order_by(Turn.created_at.asc())
        ).all()
    )
    if not turns:
        return 0

    if mode == "incremental":
        used_turn_ids = {
            tid
            for span in db.scalars(select(Span).where(Span.conversation_id == conversation_id)).all()
            for tid in (span.source_turn_ids_json or [])
        }
        candidate_turns = [t for t in turns if t.turn_id not in used_turn_ids]
    else:
        db.query(Span).filter(Span.conversation_id == conversation_id).delete()
        candidate_turns = turns

    created = 0
    for turn in candidate_turns:
        chunks = _chunk_turn(turn)
        for chunk_text, chunk_tokens in chunks:
            thread_id, decision = _assign_thread(db, conversation_id, chunk_text, turn.thread_hint)
            span = Span(
                conversation_id=conversation_id,
                source_turn_ids_json=[turn.turn_id],
                text=chunk_text,
                token_count_est=chunk_tokens,
                thread_id=thread_id,
                span_type="tool_output" if turn.speaker == "tool" else "dialog",
                trust_score=0.8,
                trust_reason="default",
            )
            db.add(span)
            db.flush()
            created += 1
            log_pipeline(
                db,
                conversation_id,
                pipeline="segmentation",
                stage="assign_thread",
                details={
                    "turn_id": turn.turn_id,
                    "span_id": span.span_id,
                    "thread_id": thread_id,
                    "decision": decision,
                    "token_count_est": chunk_tokens,
                },
            )

    _refresh_thread_stats(db, conversation_id)
    db.flush()
    return created


def retokenize_spans(db: Session, conversation_id: str) -> None:
    spans = list(db.scalars(select(Span).where(Span.conversation_id == conversation_id)).all())
    for span in spans:
        span.token_count_est = token_count_est(span.text)
    db.flush()
