from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Span
from app.deps import db_session, require_api_key
from app.schemas import SpanOut
from app.services.serializers import span_out

router = APIRouter(tags=["spans"], dependencies=[Depends(require_api_key)])


@router.get("/conversations/{conversation_id}/spans", response_model=list[SpanOut])
def list_spans(
    conversation_id: str,
    thread_id: str | None = Query(default=None),
    include_quarantined: bool = Query(default=False),
    db: Session = Depends(db_session),
) -> list[SpanOut]:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt = select(Span).where(Span.conversation_id == conversation_id)
    if thread_id:
        stmt = stmt.where(Span.thread_id == thread_id)
    rows = list(db.scalars(stmt.order_by(Span.created_at.desc())).all())

    now = datetime.utcnow()
    if not include_quarantined:
        rows = [s for s in rows if not s.quarantined_until or s.quarantined_until <= now]

    return [span_out(s) for s in rows]
