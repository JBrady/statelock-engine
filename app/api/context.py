from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context_builder.builder import build_working_context
from app.db.models import Conversation, WorkingContext
from app.deps import db_session, require_api_key
from app.schemas import BuildWorkingContextRequest, WorkingContextOut
from app.services.serializers import working_context_out

router = APIRouter(tags=["context"], dependencies=[Depends(require_api_key)])


@router.post("/conversations/{conversation_id}/working_context", response_model=WorkingContextOut)
def build_context(conversation_id: str, payload: BuildWorkingContextRequest, db: Session = Depends(db_session)) -> WorkingContextOut:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    wc = build_working_context(
        db,
        conversation,
        query=payload.query,
        target_thread_mode=payload.target_thread_mode,
        pinned_thread_id=payload.pinned_thread_id,
        max_context_tokens=payload.max_context_tokens,
    )
    db.commit()
    db.refresh(wc)
    return working_context_out(wc)


@router.get("/conversations/{conversation_id}/working_context/latest", response_model=WorkingContextOut)
def latest_context(conversation_id: str, db: Session = Depends(db_session)) -> WorkingContextOut:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    wc = db.scalar(
        select(WorkingContext)
        .where(WorkingContext.conversation_id == conversation_id)
        .order_by(WorkingContext.built_at.desc())
    )
    if not wc:
        raise HTTPException(status_code=404, detail="No working context found")
    return working_context_out(wc)
