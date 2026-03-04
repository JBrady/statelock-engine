from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backends.stub_llm import StubLLMBackend
from app.db.models import Conversation, TelemetrySnapshot
from app.deps import db_session, require_api_key
from app.schemas import TelemetryListResponse, TelemetrySnapshotRequest
from app.services.serializers import telemetry_snapshot_out
from app.services.telemetry_queries import (
    ensure_conversation_exists,
    explain_snapshot,
    get_recent_run_groups,
    get_recent_snapshots,
    get_run_group_details,
)
from app.services.telemetry_service import run_telemetry

router = APIRouter(tags=["telemetry"], dependencies=[Depends(require_api_key)])
backend = StubLLMBackend()


@router.post("/conversations/{conversation_id}/telemetry", response_model=TelemetryListResponse)
def telemetry(conversation_id: str, payload: TelemetrySnapshotRequest, db: Session = Depends(db_session)) -> TelemetryListResponse:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    snapshots = run_telemetry(
        db,
        conversation=conversation,
        turn_id=payload.turn_id,
        query=payload.query,
        mode_override=payload.mode,
        backend=backend,
    )
    db.commit()
    for s in snapshots:
        db.refresh(s)
    return TelemetryListResponse(snapshots=[telemetry_snapshot_out(s) for s in snapshots])


@router.get("/conversations/{conversation_id}/telemetry/latest", response_model=TelemetryListResponse)
def latest_telemetry(conversation_id: str, db: Session = Depends(db_session)) -> TelemetryListResponse:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    latest = db.scalar(
        select(TelemetrySnapshot)
        .where(TelemetrySnapshot.conversation_id == conversation_id)
        .order_by(TelemetrySnapshot.created_at.desc(), TelemetrySnapshot.snapshot_id.desc())
    )
    if not latest:
        return TelemetryListResponse(snapshots=[])

    rows = list(
        db.scalars(
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.conversation_id == conversation_id)
            .where(TelemetrySnapshot.run_group_id == latest.run_group_id)
            .order_by(TelemetrySnapshot.created_at.desc(), TelemetrySnapshot.snapshot_id.desc())
        ).all()
    )
    return TelemetryListResponse(snapshots=[telemetry_snapshot_out(r) for r in rows])


@router.get("/conversations/{conversation_id}/telemetry/recent", response_model=TelemetryListResponse)
def telemetry_recent(
    conversation_id: str,
    limit: int = 20,
    include_actions: bool = True,
    db: Session = Depends(db_session),
) -> TelemetryListResponse:
    if not ensure_conversation_exists(db, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    snapshots = get_recent_snapshots(
        db,
        conversation_id=conversation_id,
        limit=limit,
        include_actions=include_actions,
    )
    return TelemetryListResponse(snapshots=snapshots)


@router.get("/conversations/{conversation_id}/telemetry/run_groups/recent", response_model=dict)
def telemetry_run_groups_recent(
    conversation_id: str,
    limit: int = 20,
    db: Session = Depends(db_session),
) -> dict:
    if not ensure_conversation_exists(db, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    groups = get_recent_run_groups(db, conversation_id=conversation_id, limit=limit)
    return {"run_groups": groups}


@router.get("/conversations/{conversation_id}/telemetry/run_groups/{run_group_id}", response_model=TelemetryListResponse)
def telemetry_run_group_detail(
    conversation_id: str,
    run_group_id: str,
    include_actions: bool = True,
    db: Session = Depends(db_session),
) -> TelemetryListResponse:
    if not ensure_conversation_exists(db, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = get_run_group_details(db, conversation_id=conversation_id, run_group_id=run_group_id)
    snapshots = []
    for row in rows:
        snap = telemetry_snapshot_out(row)
        if not include_actions:
            snap.actions_taken = {"rebuilt_context": False, "quarantined_spans": [], "notes": ""}
        snapshots.append(snap)
    return TelemetryListResponse(snapshots=snapshots)


@router.get("/conversations/{conversation_id}/telemetry/snapshots/{snapshot_id}/explain", response_model=dict)
def telemetry_snapshot_explain(
    conversation_id: str,
    snapshot_id: str,
    db: Session = Depends(db_session),
) -> dict:
    if not ensure_conversation_exists(db, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    explained = explain_snapshot(db, conversation_id=conversation_id, snapshot_id=snapshot_id)
    if not explained:
        raise HTTPException(status_code=404, detail="Telemetry snapshot not found")
    return explained
