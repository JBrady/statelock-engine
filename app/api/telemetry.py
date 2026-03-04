from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backends.stub_llm import StubLLMBackend
from app.db.models import Conversation, TelemetrySnapshot
from app.deps import db_session, require_api_key
from app.schemas import TelemetryListResponse, TelemetrySnapshotRequest
from app.services.serializers import telemetry_snapshot_out
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
        .order_by(TelemetrySnapshot.created_at.desc())
    )
    if not latest:
        return TelemetryListResponse(snapshots=[])

    rows = list(
        db.scalars(
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.run_group_id == latest.run_group_id)
            .order_by(TelemetrySnapshot.method.asc())
        ).all()
    )
    return TelemetryListResponse(snapshots=[telemetry_snapshot_out(r) for r in rows])
