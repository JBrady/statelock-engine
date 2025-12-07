from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import MemoryCreate, MemoryResponse, MemoryQuery, MemoryQueryResponse, BulkDeleteRequest
from app.services.memory_service import MemoryService
from typing import List, Optional

router = APIRouter()

# Dependency to provide the service
def get_memory_service():
    return MemoryService()

@router.post("/", response_model=MemoryResponse, status_code=201)
def add_memory(memory: MemoryCreate, service: MemoryService = Depends(get_memory_service)):
    """
    Synchronous endpoint (def) to allow FastAPI to run it in a threadpool.
    This prevents blocking the event loop during heavy embedding/DB operations.
    """
    try:
        return service.add_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=MemoryQueryResponse)
def query_memories(query: MemoryQuery, service: MemoryService = Depends(get_memory_service)):
    try:
        results = service.query_memories(query)
        return MemoryQueryResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[MemoryResponse])
def list_memories(
    session_id: Optional[str] = None,
    limit: int = 100,
    service: MemoryService = Depends(get_memory_service)
):
    try:
        return service.list_memories(session_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bulk", status_code=200)
def delete_bulk(request: BulkDeleteRequest, service: MemoryService = Depends(get_memory_service)):
    try:
        service.delete_bulk(request.ids)
        return {"message": f"Deleted {len(request.ids)} blocks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}", status_code=200)
def delete_session(session_id: str, service: MemoryService = Depends(get_memory_service)):
    try:
        service.delete_session(session_id)
        return {"message": f"Deleted all blocks for session {session_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{block_id}", status_code=200)
def delete_memory(block_id: str, service: MemoryService = Depends(get_memory_service)):
    try:
        service.delete_memory(block_id)
        return {"message": f"Deleted block {block_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
