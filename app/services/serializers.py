from __future__ import annotations

from app.db import models
from app.schemas import (
    ConversationOut,
    ConversationSettings,
    MemoryEntryOut,
    SpanOut,
    TelemetrySnapshotOut,
    ThreadOut,
    TurnOut,
    WorkingContextOut,
)


def conversation_out(c: models.Conversation) -> ConversationOut:
    return ConversationOut(
        conversation_id=c.conversation_id,
        created_at=c.created_at,
        updated_at=c.updated_at,
        title=c.title,
        tags=c.tags_json or [],
        notes=c.notes,
        settings=ConversationSettings(
            max_context_tokens=c.max_context_tokens,
            telemetry_mode=c.telemetry_mode,
            target_thread_mode=c.target_thread_mode,
            pinned_thread_id=c.pinned_thread_id,
        ),
    )


def turn_out(t: models.Turn) -> TurnOut:
    return TurnOut.model_validate(t)


def thread_out(t: models.Thread) -> ThreadOut:
    return ThreadOut(
        thread_id=t.thread_id,
        conversation_id=t.conversation_id,
        name=t.name,
        summary=t.summary,
        created_at=t.created_at,
        updated_at=t.updated_at,
        span_count=t.span_count,
        last_activity_at=t.last_activity_at,
    )


def working_context_out(w: models.WorkingContext) -> WorkingContextOut:
    return WorkingContextOut(
        working_context_id=w.working_context_id,
        conversation_id=w.conversation_id,
        built_at=w.built_at,
        target_thread_id=w.target_thread_id,
        selected_span_ids=w.selected_span_ids_json or [],
        assembled_text=w.assembled_text,
        token_count_est=w.token_count_est,
        rationale={
            "selection_method": w.selection_method,
            "selection_log": w.selection_log_json or {},
        },
    )


def telemetry_snapshot_out(s: models.TelemetrySnapshot) -> TelemetrySnapshotOut:
    return TelemetrySnapshotOut(
        snapshot_id=s.snapshot_id,
        conversation_id=s.conversation_id,
        turn_id=s.turn_id,
        run_group_id=s.run_group_id,
        created_at=s.created_at,
        target_thread_id=s.target_thread_id,
        method=s.method,
        proxy_kind=s.proxy_kind,
        spans_considered=s.spans_considered_json or [],
        influence={"weights": s.weights_json or []},
        metrics=s.metrics_json or {},
        actions_taken=s.actions_taken_json or {},
    )


def memory_entry_out(m: models.MemoryEntry) -> MemoryEntryOut:
    return MemoryEntryOut(
        memory_id=m.memory_id,
        conversation_id=m.conversation_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
        memory_type=m.memory_type,
        title=m.title,
        content=m.content,
        tags=m.tags_json or [],
        strength=m.strength,
        status=m.status,
        provenance={
            "source_turn_ids": m.source_turn_ids_json or [],
            "source_span_ids": m.source_span_ids_json or [],
        },
        eval={
            "success_count": m.success_count,
            "failure_count": m.failure_count,
            "last_applied_at": m.last_applied_at,
        },
    )


def span_out(s: models.Span) -> SpanOut:
    return SpanOut(
        span_id=s.span_id,
        conversation_id=s.conversation_id,
        created_at=s.created_at,
        source_turn_ids=s.source_turn_ids_json or [],
        text=s.text,
        token_count_est=s.token_count_est,
        thread_id=s.thread_id,
        span_type=s.span_type,
        trust={"score": s.trust_score, "reason": s.trust_reason},
        recency={"last_used_at": s.last_used_at, "first_seen_at": s.first_seen_at},
        links={
            "semantic_neighbors": s.semantic_neighbors_json or [],
            "provenance": s.provenance_json or [],
            "contradictions": s.contradictions_json or [],
        },
        quarantined_until=s.quarantined_until,
    )
