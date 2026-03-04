from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Thread
from app.deps import db_session, require_api_key
from app.pipelines.segmentation import segment_conversation
from app.schemas import SegmentConversationRequest, SegmentConversationResponse
from app.services.serializers import thread_out
from app.schemas import ThreadOut

router = APIRouter(tags=["segmentation"], dependencies=[Depends(require_api_key)])


@router.post("/conversations/{conversation_id}/segment", response_model=SegmentConversationResponse)
def segment(conversation_id: str, payload: SegmentConversationRequest, db: Session = Depends(db_session)) -> SegmentConversationResponse:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    created = segment_conversation(db, conversation_id=conversation_id, mode=payload.mode)
    db.commit()

    threads = list(db.scalars(select(Thread).where(Thread.conversation_id == conversation_id)).all())
    return SegmentConversationResponse(spans_created=created, threads=[thread_out(t) for t in threads])


@router.get("/conversations/{conversation_id}/threads", response_model=list[ThreadOut])
def list_threads(conversation_id: str, db: Session = Depends(db_session)):
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    rows = list(db.scalars(select(Thread).where(Thread.conversation_id == conversation_id).order_by(Thread.last_activity_at.desc())).all())
    return [thread_out(t) for t in rows]
