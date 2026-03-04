from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation
from app.deps import db_session, require_api_key
from app.schemas import ConversationOut, CreateConversationRequest
from app.services.serializers import conversation_out

router = APIRouter(prefix="/conversations", tags=["conversations"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=ConversationOut)
def create_conversation(payload: CreateConversationRequest, db: Session = Depends(db_session)) -> ConversationOut:
    settings = payload.settings
    c = Conversation(
        title=payload.title,
        max_context_tokens=settings.max_context_tokens if settings else 6000,
        telemetry_mode=settings.telemetry_mode if settings else "standard",
        target_thread_mode=settings.target_thread_mode if settings else "auto",
        pinned_thread_id=settings.pinned_thread_id if settings else None,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return conversation_out(c)


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(db_session)) -> list[ConversationOut]:
    rows = list(db.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all())
    return [conversation_out(c) for c in rows]


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(db_session)) -> ConversationOut:
    c = db.get(Conversation, conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation_out(c)


@router.patch("/{conversation_id}", response_model=ConversationOut)
def update_conversation(conversation_id: str, payload: CreateConversationRequest, db: Session = Depends(db_session)) -> ConversationOut:
    c = db.get(Conversation, conversation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")
    c.title = payload.title
    if payload.settings:
        c.max_context_tokens = payload.settings.max_context_tokens
        c.telemetry_mode = payload.settings.telemetry_mode
        c.target_thread_mode = payload.settings.target_thread_mode
        c.pinned_thread_id = payload.settings.pinned_thread_id
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return conversation_out(c)
