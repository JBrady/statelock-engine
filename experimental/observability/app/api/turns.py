from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Turn
from app.deps import db_session, require_api_key
from app.schemas import AddTurnRequest, TurnOut
from app.services.serializers import turn_out
from app.utils import token_count_est

router = APIRouter(tags=["turns"], dependencies=[Depends(require_api_key)])


@router.post("/conversations/{conversation_id}/turns", response_model=TurnOut)
def add_turn(conversation_id: str, payload: AddTurnRequest, db: Session = Depends(db_session)) -> TurnOut:
    c = db.get(Conversation, conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")

    turn = Turn(
        conversation_id=conversation_id,
        speaker=payload.speaker,
        text=payload.text,
        tool_name=payload.tool_name,
        tool_payload_ref=payload.tool_payload_ref,
        thread_hint=payload.thread_hint,
        token_count=token_count_est(payload.text),
    )
    db.add(turn)
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(turn)
    return turn_out(turn)


@router.get("/conversations/{conversation_id}/turns", response_model=list[TurnOut])
def list_turns(conversation_id: str, db: Session = Depends(db_session)) -> list[TurnOut]:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    turns = list(
        db.scalars(select(Turn).where(Turn.conversation_id == conversation_id).order_by(Turn.created_at.asc())).all()
    )
    return [turn_out(t) for t in turns]
