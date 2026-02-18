from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_api_key
from app.core.config import settings
from app.models.schemas import (
    BulkDeleteRequest,
    HybridMemoryQuery,
    MemoryCreate,
    MemoryQuery,
    MemoryQueryResponse,
    MemoryResponse,
    MemoryUpsert,
    PaginatedMemoriesResponse,
    SessionRestoreRequest,
    SessionRestoreResponse,
    SessionSnapshotResponse,
)
from app.services.memory_service import MemoryService

router = APIRouter(dependencies=[Depends(require_api_key)])


def get_memory_service() -> MemoryService:
    return MemoryService()


@router.post("/", response_model=MemoryResponse, status_code=201)
def add_memory(memory: MemoryCreate, service: MemoryService = Depends(get_memory_service)):
    return service.add_memory(memory)


@router.post("/upsert", response_model=MemoryResponse, status_code=200)
def upsert_memory(memory: MemoryUpsert, service: MemoryService = Depends(get_memory_service)):
    return service.upsert_memory(memory)


@router.post("/query", response_model=MemoryQueryResponse)
def query_memories(query: MemoryQuery, service: MemoryService = Depends(get_memory_service)):
    results = service.query_memories(query)
    return MemoryQueryResponse(results=results)


@router.post("/query-hybrid", response_model=MemoryQueryResponse)
def query_memories_hybrid(
    query: HybridMemoryQuery,
    service: MemoryService = Depends(get_memory_service),
):
    results = service.query_memories_hybrid(query)
    return MemoryQueryResponse(results=results)


@router.get("/", response_model=PaginatedMemoriesResponse)
def list_memories(
    session_id: Optional[str] = None,
    limit: int = Query(default=settings.API_DEFAULT_PAGE_SIZE, ge=1, le=settings.API_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    service: MemoryService = Depends(get_memory_service),
):
    items = service.list_memories(session_id=session_id, limit=limit, offset=offset)
    total = service.count_memories(session_id=session_id)
    return PaginatedMemoriesResponse(items=items, limit=limit, offset=offset, total=total)


@router.delete("/bulk", status_code=200)
def delete_bulk(request: BulkDeleteRequest, service: MemoryService = Depends(get_memory_service)):
    service.delete_bulk(request.ids)
    return {"message": f"Deleted {len(request.ids)} blocks."}


@router.delete("/session/{session_id}", status_code=200)
def delete_session(session_id: str, service: MemoryService = Depends(get_memory_service)):
    service.delete_session(session_id)
    return {"message": f"Deleted all blocks for session {session_id}."}


@router.get("/session/{session_id}/snapshot", response_model=SessionSnapshotResponse)
def snapshot_session(
    session_id: str,
    limit: int = Query(default=1000, ge=1, le=10000),
    service: MemoryService = Depends(get_memory_service),
):
    return service.snapshot_session(session_id=session_id, limit=limit)


@router.post("/session/{session_id}/restore", response_model=SessionRestoreResponse)
def restore_session(
    session_id: str,
    request: SessionRestoreRequest,
    service: MemoryService = Depends(get_memory_service),
):
    restored = service.restore_session(session_id=session_id, request=request)
    return SessionRestoreResponse(session_id=session_id, restored=restored, mode=request.mode)


@router.delete("/{block_id}", status_code=200)
def delete_memory(block_id: str, service: MemoryService = Depends(get_memory_service)):
    service.delete_memory(block_id)
    return {"message": f"Deleted block {block_id}."}
