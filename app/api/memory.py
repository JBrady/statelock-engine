from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, MemoryEntry
from app.deps import db_session, require_api_key
from app.memory.distill import distill_memory
from app.schemas import MemoryDistillRequest, MemoryDistillResponse, MemoryEntryOut
from app.services.serializers import memory_entry_out

router = APIRouter(tags=["memory"], dependencies=[Depends(require_api_key)])


@router.get("/memory", response_model=list[MemoryEntryOut])
def memory_list(
    conversation_id: str | None = Query(default=None),
    memory_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> list[MemoryEntryOut]:
    stmt = select(MemoryEntry)
    if conversation_id is not None:
        stmt = stmt.where(MemoryEntry.conversation_id == conversation_id)
    if memory_type is not None:
        stmt = stmt.where(MemoryEntry.memory_type == memory_type)
    if status is not None:
        stmt = stmt.where(MemoryEntry.status == status)
    rows = list(db.scalars(stmt.order_by(MemoryEntry.updated_at.desc())).all())
    return [memory_entry_out(m) for m in rows]


@router.post("/conversations/{conversation_id}/memory/distill", response_model=MemoryDistillResponse)
def memory_distill(conversation_id: str, payload: MemoryDistillRequest, db: Session = Depends(db_session)) -> MemoryDistillResponse:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    created, merged, quarantined = distill_memory(db, conversation_id, payload.trigger)
    db.commit()
    return MemoryDistillResponse(
        created_memory_ids=created,
        merged_memory_ids=merged,
        quarantined_memory_ids=quarantined,
    )
