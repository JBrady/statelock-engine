from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.utcnow()


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    title: Mapped[str] = mapped_column(String, default="Untitled")
    tags_json: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    max_context_tokens: Mapped[int] = mapped_column(Integer, default=6000)
    telemetry_mode: Mapped[str] = mapped_column(String, default="standard")
    target_thread_mode: Mapped[str] = mapped_column(String, default="auto")
    pinned_thread_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Turn(Base):
    __tablename__ = "turns"

    turn_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    speaker: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_payload_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thread_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    importance_hint: Mapped[float | None] = mapped_column(Float, nullable=True)


class Span(Base):
    __tablename__ = "spans"

    span_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    source_turn_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    text: Mapped[str] = mapped_column(Text)
    token_count_est: Mapped[int] = mapped_column(Integer)
    thread_id: Mapped[str] = mapped_column(String, index=True)
    span_type: Mapped[str] = mapped_column(String, default="dialog")
    trust_score: Mapped[float] = mapped_column(Float, default=0.8)
    trust_reason: Mapped[str] = mapped_column(String, default="default")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    semantic_neighbors_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[list] = mapped_column(JSON, default=list)
    contradictions_json: Mapped[list] = mapped_column(JSON, default=list)
    quarantined_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    thread_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    span_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class WorkingContext(Base):
    __tablename__ = "working_contexts"

    working_context_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    built_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    target_thread_id: Mapped[str] = mapped_column(String)
    selected_span_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    assembled_text: Mapped[str] = mapped_column(Text)
    token_count_est: Mapped[int] = mapped_column(Integer)
    selection_method: Mapped[str] = mapped_column(String, default="heuristic")
    selection_log_json: Mapped[dict] = mapped_column(JSON, default=dict)


class TelemetrySnapshot(Base):
    __tablename__ = "telemetry_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), index=True)
    turn_id: Mapped[str] = mapped_column(ForeignKey("turns.turn_id"), index=True)
    run_group_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    target_thread_id: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    proxy_kind: Mapped[str | None] = mapped_column(String, nullable=True)
    spans_considered_json: Mapped[list] = mapped_column(JSON, default=list)
    weights_json: Mapped[list] = mapped_column(JSON, default=list)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    actions_taken_json: Mapped[dict] = mapped_column(JSON, default=dict)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    memory_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    memory_type: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    tags_json: Mapped[list] = mapped_column(JSON, default=list)
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String, default="active", index=True)
    source_turn_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    source_span_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GovernanceEvent(Base):
    __tablename__ = "governance_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    log_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    pipeline: Mapped[str] = mapped_column(String)
    stage: Mapped[str] = mapped_column(String)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
