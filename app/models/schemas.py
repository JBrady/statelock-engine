from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MemoryBase(BaseModel):
    content: str = Field(..., description="The text content of the memory block.")
    name: Optional[str] = Field(None, description="An optional descriptive name.")
    session_id: str = Field("default", description="The session ID this memory belongs to.")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization.")

class MemoryCreate(MemoryBase):
    pass

class MemoryResponse(MemoryBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    distance: Optional[float] = None

class MemoryQuery(BaseModel):
    query_text: str
    session_id: Optional[str] = Field(None, description="Filter by session ID. If None, searches all.")
    top_k: int = Field(default=3, gt=0, description="Number of results.")

class MemoryQueryResponse(BaseModel):
    results: List[MemoryResponse]

class BulkDeleteRequest(BaseModel):
    ids: List[str]
