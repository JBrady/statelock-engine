from fastapi import APIRouter, Depends, Query

from app.core.auth import require_api_key
from app.models.schemas import SessionsResponse, StatsOverviewResponse, TagsResponse
from app.services.memory_service import MemoryService

router = APIRouter(dependencies=[Depends(require_api_key)])


def get_memory_service() -> MemoryService:
    return MemoryService()


@router.get("/stats/overview", response_model=StatsOverviewResponse)
def get_stats_overview(
    top_tags_limit: int = Query(default=5, ge=1, le=20),
    service: MemoryService = Depends(get_memory_service),
):
    return service.stats_overview(top_tags_limit=top_tags_limit)


@router.get("/sessions", response_model=SessionsResponse)
def list_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: MemoryService = Depends(get_memory_service),
):
    items, total = service.list_sessions(limit=limit, offset=offset)
    return SessionsResponse(items=items, limit=limit, offset=offset, total=total)


@router.get("/tags", response_model=TagsResponse)
def list_tags(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: MemoryService = Depends(get_memory_service),
):
    items, total = service.list_tags(limit=limit, offset=offset)
    return TagsResponse(items=items, limit=limit, offset=offset, total=total)
