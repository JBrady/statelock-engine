from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, GovernanceEvent, TelemetrySnapshot
from app.deps import db_session, require_api_key
from app.governance.actions import apply_governance, unquarantine_span
from app.schemas import GovernanceApplyRequest, GovernanceApplyResponse, UnquarantineResponse
from app.services.serializers import working_context_out

router = APIRouter(tags=["governance"], dependencies=[Depends(require_api_key)])


@router.post("/conversations/{conversation_id}/governance/apply", response_model=GovernanceApplyResponse)
def governance_apply(conversation_id: str, payload: GovernanceApplyRequest, db: Session = Depends(db_session)) -> GovernanceApplyResponse:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    snapshot = db.get(TelemetrySnapshot, payload.snapshot_id) if payload.snapshot_id else None
    rebuilt, quarantined, wc = apply_governance(db, conversation, snapshot, payload.actions)
    db.commit()
    return GovernanceApplyResponse(
        rebuilt_context=rebuilt,
        quarantined_spans=quarantined,
        working_context=working_context_out(wc) if wc else None,
    )


@router.get("/conversations/{conversation_id}/governance/log", response_model=list[dict])
def governance_log(conversation_id: str, db: Session = Depends(db_session)):
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    rows = list(
        db.scalars(
            select(GovernanceEvent)
            .where(GovernanceEvent.conversation_id == conversation_id)
            .order_by(GovernanceEvent.created_at.desc())
        ).all()
    )
    return [
        {
            "event_id": r.event_id,
            "created_at": r.created_at,
            "event_type": r.event_type,
            "snapshot_id": r.snapshot_id,
            "details": r.details_json,
        }
        for r in rows
    ]


@router.post("/conversations/{conversation_id}/spans/{span_id}/unquarantine", response_model=UnquarantineResponse)
def unquarantine(conversation_id: str, span_id: str, db: Session = Depends(db_session)) -> UnquarantineResponse:
    ok = unquarantine_span(db, conversation_id, span_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Span not found")
    db.commit()
    return UnquarantineResponse(span_id=span_id, unquarantined=True)
