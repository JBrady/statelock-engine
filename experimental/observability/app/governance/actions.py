from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context_builder.builder import ContextBuildOptions, build_working_context
from app.db.models import Conversation, GovernanceEvent, Span, TelemetrySnapshot, Turn


def _latest_snapshot(db: Session, conversation_id: str) -> TelemetrySnapshot | None:
    return db.scalar(
        select(TelemetrySnapshot)
        .where(TelemetrySnapshot.conversation_id == conversation_id)
        .order_by(TelemetrySnapshot.created_at.desc())
    )


def _latest_user_query(db: Session, conversation_id: str) -> str:
    t = db.scalar(
        select(Turn)
        .where(Turn.conversation_id == conversation_id, Turn.speaker == "user")
        .order_by(Turn.created_at.desc())
    )
    return t.text if t else ""


def apply_governance(
    db: Session,
    conversation: Conversation,
    snapshot: TelemetrySnapshot | None,
    action_overrides: dict | None = None,
) -> tuple[bool, list[str], object | None]:
    snap = snapshot or _latest_snapshot(db, conversation.conversation_id)
    if not snap:
        return False, [], None

    alarms = (snap.metrics_json or {}).get("alarms", {})
    rows = snap.weights_json or []

    quarantined: list[str] = []
    rebuilt = False
    query = _latest_user_query(db, conversation.conversation_id)
    options = ContextBuildOptions()

    if alarms.get("off_thread_spike"):
        for row in rows:
            if row.get("thread_id") != snap.target_thread_id and row.get("w", 0.0) >= 0.08:
                span = db.get(Span, row["span_id"])
                if span:
                    span.quarantined_until = datetime.utcnow() + timedelta(minutes=60)
                    quarantined.append(span.span_id)
        options.restrict_to_target_thread = True
        rebuilt = True

    if alarms.get("anchor_rot") and rows:
        top = max(rows, key=lambda r: r.get("w", 0.0))
        span = db.get(Span, top["span_id"])
        if span:
            span.trust_score = max(0.0, span.trust_score - 0.2)
            rebuilt = True

    if alarms.get("smear_rot"):
        options.max_spans_delta -= 6
        options.similarity_threshold_delta += 0.08
        rebuilt = True

    if action_overrides:
        if action_overrides.get("rebuild_context") is True:
            rebuilt = True
        if action_overrides.get("restrict_to_target_thread") is True:
            options.restrict_to_target_thread = True

    working_context = None
    if rebuilt:
        working_context = build_working_context(db, conversation, query=query or "", options=options)

    snap.actions_taken_json = {
        "rebuilt_context": rebuilt,
        "quarantined_spans": quarantined,
        "notes": "governance applied",
    }

    db.add(
        GovernanceEvent(
            conversation_id=conversation.conversation_id,
            snapshot_id=snap.snapshot_id,
            event_type="governance_apply",
            details_json={
                "alarms": alarms,
                "rebuilt_context": rebuilt,
                "quarantined_spans": quarantined,
                "options": {
                    "restrict_to_target_thread": options.restrict_to_target_thread,
                    "max_spans_delta": options.max_spans_delta,
                    "similarity_threshold_delta": options.similarity_threshold_delta,
                },
            },
        )
    )
    db.flush()

    return rebuilt, quarantined, working_context


def unquarantine_span(db: Session, conversation_id: str, span_id: str) -> bool:
    span = db.get(Span, span_id)
    if not span or span.conversation_id != conversation_id:
        return False
    span.quarantined_until = None
    db.add(
        GovernanceEvent(
            conversation_id=conversation_id,
            snapshot_id=None,
            event_type="manual_unquarantine",
            details_json={"span_id": span_id},
        )
    )
    db.flush()
    return True
