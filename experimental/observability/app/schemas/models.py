from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelBase(BaseModel):
    model_config = {"from_attributes": True}


class ConversationSettings(BaseModel):
    max_context_tokens: int = 6000
    telemetry_mode: Literal["off", "minimal", "standard", "verbose"] = "standard"
    target_thread_mode: Literal["auto", "pinned"] = "auto"
    pinned_thread_id: str | None = None


class CreateConversationRequest(BaseModel):
    title: str
    settings: ConversationSettings | None = None


class ConversationOut(ModelBase):
    conversation_id: str
    created_at: datetime
    updated_at: datetime
    title: str
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    settings: ConversationSettings


class AddTurnRequest(BaseModel):
    speaker: Literal["user", "assistant", "tool"]
    text: str
    tool_name: str | None = None
    tool_payload_ref: str | None = None
    thread_hint: str | None = None


class TurnOut(ModelBase):
    turn_id: str
    conversation_id: str
    created_at: datetime
    speaker: str
    text: str
    tool_name: str | None = None
    tool_payload_ref: str | None = None
    token_count: int | None = None
    thread_hint: str | None = None


class ThreadOut(ModelBase):
    thread_id: str
    conversation_id: str
    name: str
    summary: str
    created_at: datetime
    updated_at: datetime
    span_count: int
    last_activity_at: datetime


class SegmentConversationRequest(BaseModel):
    mode: Literal["incremental", "full"] = "incremental"


class SegmentConversationResponse(BaseModel):
    spans_created: int
    threads: list[ThreadOut]


class BuildWorkingContextRequest(BaseModel):
    query: str
    target_thread_mode: Literal["auto", "pinned"] | None = None
    pinned_thread_id: str | None = None
    max_context_tokens: int | None = None


class WorkingContextOut(ModelBase):
    working_context_id: str
    conversation_id: str
    built_at: datetime
    target_thread_id: str
    selected_span_ids: list[str]
    assembled_text: str
    token_count_est: int
    rationale: dict[str, Any]


class TelemetrySnapshotRequest(BaseModel):
    turn_id: str
    query: str
    mode: Literal["minimal", "standard", "verbose"] | None = None


class TelemetrySnapshotOut(ModelBase):
    snapshot_id: str
    conversation_id: str
    turn_id: str
    run_group_id: str
    created_at: datetime
    target_thread_id: str
    method: Literal["grad_proxy", "ablation_kl"]
    proxy_kind: Literal["gradients", "attention", "lexical"] | None = None
    spans_considered: list[str]
    influence: dict[str, Any]
    metrics: dict[str, Any]
    actions_taken: dict[str, Any]


class GovernanceApplyRequest(BaseModel):
    snapshot_id: str | None = None
    actions: dict[str, Any] | None = None


class GovernanceApplyResponse(BaseModel):
    rebuilt_context: bool
    quarantined_spans: list[str]
    working_context: WorkingContextOut | None


class MemoryEntryOut(ModelBase):
    memory_id: str
    conversation_id: str | None
    created_at: datetime
    updated_at: datetime
    memory_type: Literal["episodic", "semantic", "procedural"]
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    strength: float
    status: Literal["active", "deprecated", "quarantined"]
    provenance: dict[str, Any]
    eval: dict[str, Any]


class MemoryDistillRequest(BaseModel):
    trigger: Literal["user_done", "assistant_done", "timer"]


class MemoryDistillResponse(BaseModel):
    created_memory_ids: list[str]
    merged_memory_ids: list[str]
    quarantined_memory_ids: list[str]


class SpanOut(ModelBase):
    span_id: str
    conversation_id: str
    created_at: datetime
    source_turn_ids: list[str]
    text: str
    token_count_est: int
    thread_id: str
    span_type: str
    trust: dict[str, Any]
    recency: dict[str, Any]
    links: dict[str, Any]
    quarantined_until: datetime | None


class UnquarantineResponse(BaseModel):
    span_id: str
    unquarantined: bool


class TelemetryListResponse(BaseModel):
    snapshots: list[TelemetrySnapshotOut]
