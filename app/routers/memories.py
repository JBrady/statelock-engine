from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import MemoryCreate, MemoryResponse, MemoryQuery, MemoryQueryResponse, BulkDeleteRequest
from app.services.memory_service import MemoryService
from typing import List, Optional

router = APIRouter()
service = MemoryService()

@router.post("/", response_model=MemoryResponse, status_code=201)
async def add_memory(memory: MemoryCreate):
    try:
        return service.add_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=MemoryQueryResponse)
async def query_memories(query: MemoryQuery):
    try:
        results = service.query_memories(query)
        return MemoryQueryResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[MemoryResponse])
async def list_memories(session_id: Optional[str] = None, limit: int = 100):
    try:
        return service.list_memories(session_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bulk", status_code=200)
async def delete_bulk(request: BulkDeleteRequest):
    try:
        service.delete_bulk(request.ids)
        return {"message": f"Deleted {len(request.ids)} blocks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}", status_code=200)
async def delete_session(session_id: str):
    try:
        service.delete_session(session_id)
        return {"message": f"Deleted all blocks for session {session_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{block_id}", status_code=200)
async def delete_memory(block_id: str):
    try:
        service.delete_memory(block_id)
        return {"message": f"Deleted block {block_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
