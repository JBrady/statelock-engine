import uuid
from datetime import datetime
from typing import List, Optional
from app.core.database import get_db_collection
from app.services.embedder import get_embedder
from app.models.schemas import MemoryCreate, MemoryResponse, MemoryQuery

class MemoryService:
    def __init__(self):
        self.collection = get_db_collection()
        self.embedder = get_embedder()

    def add_memory(self, memory: MemoryCreate) -> MemoryResponse:
        block_id = str(uuid.uuid4())
        embedding = self.embedder.encode(memory.content)
        now = datetime.utcnow().isoformat()

        metadata = {
            "name": memory.name or "Unnamed Block",
            "session_id": memory.session_id,
            "created_at": now,
            "updated_at": now,
            "tags": ",".join(memory.tags) # ChromaDB metadata must be primitive types
        }

        self.collection.add(
            ids=[block_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[memory.content]
        )

        return MemoryResponse(
            id=block_id,
            content=memory.content,
            name=memory.name,
            session_id=memory.session_id,
            tags=memory.tags,
            created_at=now,
            updated_at=now
        )

    def query_memories(self, query: MemoryQuery) -> List[MemoryResponse]:
        query_embedding = self.embedder.encode(query.query_text)

        where_clause = {}
        if query.session_id:
            where_clause["session_id"] = query.session_id

        # If where_clause is empty, pass None to avoid ChromaDB errors if it expects strictly non-empty
        # But ChromaDB handles empty dict as "no filter" usually?
        # Actually for 'where', None is better than empty dict if we want no filter.
        filter_arg = where_clause if where_clause else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=query.top_k,
            where=filter_arg,
            include=['metadatas', 'distances', 'documents']
        )

        formatted_results = []
        if results and results['ids']:
            ids = results['ids'][0]
            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]

            for i in range(len(ids)):
                meta = metadatas[i]
                tags_str = meta.get("tags", "")
                tags = tags_str.split(",") if tags_str else []

                formatted_results.append(MemoryResponse(
                    id=ids[i],
                    content=documents[i],
                    name=meta.get("name"),
                    session_id=meta.get("session_id", "default"),
                    tags=tags,
                    created_at=meta.get("created_at"),
                    updated_at=meta.get("updated_at"),
                    distance=distances[i]
                ))

        return formatted_results

    def list_memories(self, session_id: Optional[str] = None, limit: int = 100) -> List[MemoryResponse]:
        where_clause = {"session_id": session_id} if session_id else None

        # .get() in ChromaDB
        results = self.collection.get(
            where=where_clause,
            limit=limit,
            include=['metadatas', 'documents']
        )

        formatted_results = []
        if results and results['ids']:
            ids = results['ids']
            metadatas = results['metadatas']
            documents = results['documents']

            for i in range(len(ids)):
                meta = metadatas[i]
                tags_str = meta.get("tags", "")
                tags = tags_str.split(",") if tags_str else []

                formatted_results.append(MemoryResponse(
                    id=ids[i],
                    content=documents[i],
                    name=meta.get("name"),
                    session_id=meta.get("session_id", "default"),
                    tags=tags,
                    created_at=meta.get("created_at"),
                    updated_at=meta.get("updated_at")
                ))
        return formatted_results

    def delete_memory(self, block_id: str):
        self.collection.delete(ids=[block_id])

    def delete_bulk(self, ids: List[str]):
        self.collection.delete(ids=ids)

    def delete_session(self, session_id: str):
        self.collection.delete(where={"session_id": session_id})
