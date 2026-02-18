from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    content: str = Field(..., min_length=1, description="The text content of the memory block.")
    name: Optional[str] = Field(None, description="An optional descriptive name.")
    session_id: str = Field(
        "default",
        min_length=1,
        description="The session ID this memory belongs to.",
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization.")


class MemoryCreate(MemoryBase):
    pass


class MemoryUpsert(MemoryBase):
    id: Optional[str] = Field(
        None,
        description="Deterministic memory id. If omitted, generated from session/name/content.",
    )
    external_id: Optional[str] = Field(
        None,
        description="Stable external identifier used to derive deterministic id.",
    )


class MemoryResponse(MemoryBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    distance: Optional[float] = None
    score: Optional[float] = None


class MemoryQuery(BaseModel):
    query_text: str = Field(..., min_length=1)
    session_id: Optional[str] = Field(
        None,
        description="Filter by session ID. If None, searches all.",
    )
    top_k: int = Field(default=3, gt=0, le=100, description="Number of results.")


class HybridMemoryQuery(MemoryQuery):
    candidate_k: int = Field(default=20, gt=0, le=500)
    recency_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    similarity_weight: float = Field(default=0.75, ge=0.0, le=1.0)


class MemoryQueryResponse(BaseModel):
    results: List[MemoryResponse]


class PaginatedMemoriesResponse(BaseModel):
    items: List[MemoryResponse]
    limit: int
    offset: int
    total: Optional[int] = None


class BulkDeleteRequest(BaseModel):
    ids: List[str] = Field(default_factory=list)


class SessionSnapshotResponse(BaseModel):
    session_id: str
    exported_at: str
    total: int
    memories: List[MemoryResponse]


class SessionRestoreRequest(BaseModel):
    mode: Literal["replace", "append"] = "append"
    memories: List[MemoryUpsert] = Field(default_factory=list)


class SessionRestoreResponse(BaseModel):
    session_id: str
    restored: int
    mode: Literal["replace", "append"]
