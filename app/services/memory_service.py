import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_db_collection
from app.core.errors import ValidationError
from app.models.schemas import (
    HybridMemoryQuery,
    MemoryCreate,
    MemoryQuery,
    MemoryResponse,
    MemoryUpsert,
    SessionRestoreRequest,
    SessionSnapshotResponse,
)
from app.services.embedder import get_embedder


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _derive_memory_id(memory: MemoryUpsert) -> str:
    if memory.id:
        return memory.id
    base = memory.external_id or f"{memory.session_id}|{memory.name or ''}|{memory.content}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]
    return f"mem_{digest}"


def _extract_tags(meta: dict) -> List[str]:
    tags_json = meta.get("tags_json")
    if isinstance(tags_json, str) and tags_json:
        try:
            parsed = json.loads(tags_json)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass

    legacy = meta.get("tags")
    if isinstance(legacy, list):
        return [str(item) for item in legacy]
    if isinstance(legacy, str) and legacy:
        return [tag for tag in legacy.split(",") if tag]
    return []


def _parse_created_at(meta: dict) -> Optional[datetime]:
    raw = meta.get("created_at")
    if not isinstance(raw, str):
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


class MemoryService:
    def __init__(self):
        self.collection = get_db_collection()
        self.embedder = get_embedder()

    def _to_response(
        self,
        item_id: str,
        document: str,
        meta: dict,
        distance: Optional[float] = None,
    ) -> MemoryResponse:
        return MemoryResponse(
            id=item_id,
            content=document,
            name=meta.get("name"),
            session_id=meta.get("session_id", "default"),
            tags=_extract_tags(meta),
            created_at=meta.get("created_at"),
            updated_at=meta.get("updated_at"),
            distance=distance,
        )

    def add_memory(self, memory: MemoryCreate) -> MemoryResponse:
        block_id = str(uuid.uuid4())
        embedding = self.embedder.encode(memory.content)
        now = _now_iso()

        metadata = {
            "name": memory.name or "Unnamed Block",
            "session_id": memory.session_id,
            "created_at": now,
            "updated_at": now,
            "tags_json": json.dumps(memory.tags),
        }

        self.collection.add(
            ids=[block_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[memory.content],
        )

        return MemoryResponse(
            id=block_id,
            content=memory.content,
            name=memory.name,
            session_id=memory.session_id,
            tags=memory.tags,
            created_at=now,
            updated_at=now,
        )

    def upsert_memory(self, memory: MemoryUpsert) -> MemoryResponse:
        block_id = _derive_memory_id(memory)
        embedding = self.embedder.encode(memory.content)
        now = _now_iso()

        existing = self.collection.get(ids=[block_id], include=["metadatas", "documents"])
        created_at = now
        if existing and existing.get("ids"):
            if existing["ids"]:
                existing_meta = (existing.get("metadatas") or [{}])[0] or {}
                created_at = existing_meta.get("created_at") or now

        metadata = {
            "name": memory.name or "Unnamed Block",
            "session_id": memory.session_id,
            "created_at": created_at,
            "updated_at": now,
            "tags_json": json.dumps(memory.tags),
        }
        if memory.external_id is not None:
            metadata["external_id"] = memory.external_id

        self.collection.upsert(
            ids=[block_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[memory.content],
        )

        return MemoryResponse(
            id=block_id,
            content=memory.content,
            name=memory.name,
            session_id=memory.session_id,
            tags=memory.tags,
            created_at=created_at,
            updated_at=now,
        )

    def query_memories(self, query: MemoryQuery) -> List[MemoryResponse]:
        query_embedding = self.embedder.encode(query.query_text)
        where_clause = {"session_id": query.session_id} if query.session_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=query.top_k,
            where=where_clause,
            include=["metadatas", "distances", "documents"],
        )

        formatted: List[MemoryResponse] = []
        if results and results.get("ids"):
            ids = results["ids"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0]
            documents = results["documents"][0]
            for i in range(len(ids)):
                formatted.append(
                    self._to_response(
                        item_id=ids[i],
                        document=documents[i],
                        meta=metadatas[i],
                        distance=distances[i],
                    )
                )
        return formatted

    def query_memories_hybrid(self, query: HybridMemoryQuery) -> List[MemoryResponse]:
        if query.recency_weight + query.similarity_weight <= 0:
            raise ValidationError("recency_weight + similarity_weight must be > 0")

        candidate_k = max(
            query.top_k,
            query.candidate_k,
            query.top_k * settings.QUERY_CANDIDATE_MULTIPLIER,
        )
        candidate_k = min(candidate_k, 500)
        candidates = self.query_memories(
            MemoryQuery(
                query_text=query.query_text,
                session_id=query.session_id,
                top_k=candidate_k,
            )
        )

        if not candidates:
            return []

        # Lower distance is better. Convert to similarity-like score.
        similarities = [(1.0 / (1.0 + (item.distance or 1.0))) for item in candidates]
        created = [_parse_created_at({"created_at": item.created_at}) for item in candidates]

        now = datetime.now(timezone.utc)
        ages_hours: List[float] = []
        for dt in created:
            if dt is None:
                ages_hours.append(1e9)
            else:
                delta = now - dt.astimezone(timezone.utc)
                ages_hours.append(max(delta.total_seconds() / 3600.0, 0.0))

        min_age = min(ages_hours)
        max_age = max(ages_hours)
        recencies: List[float] = []
        if max_age == min_age:
            recencies = [1.0 for _ in ages_hours]
        else:
            for age in ages_hours:
                recencies.append(1.0 - ((age - min_age) / (max_age - min_age)))

        scored: List[MemoryResponse] = []
        for idx, item in enumerate(candidates):
            score = (query.similarity_weight * similarities[idx]) + (
                query.recency_weight * recencies[idx]
            )
            item.score = float(score)
            scored.append(item)

        scored.sort(
            key=lambda item: (
                -(item.score or 0.0),
                -(
                    _parse_iso(item.updated_at or item.created_at)
                    or datetime.fromtimestamp(0, tz=timezone.utc)
                ).timestamp(),
                item.id,
            )
        )
        return scored[: query.top_k]

    def list_memories(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MemoryResponse]:
        where_clause = {"session_id": session_id} if session_id else None
        results = self.collection.get(
            where=where_clause,
            limit=limit,
            offset=offset,
            include=["metadatas", "documents"],
        )

        formatted: List[MemoryResponse] = []
        if results and results.get("ids"):
            ids = results["ids"]
            metadatas = results["metadatas"]
            documents = results["documents"]
            for i in range(len(ids)):
                formatted.append(
                    self._to_response(
                        item_id=ids[i],
                        document=documents[i],
                        meta=metadatas[i],
                    )
                )
        return formatted

    def count_memories(self, session_id: Optional[str] = None) -> int:
        if session_id is None:
            return int(self.collection.count())

        results = self.collection.get(where={"session_id": session_id})
        ids = results.get("ids") if results else []
        return len(ids or [])

    def snapshot_session(self, session_id: str, limit: int = 1000) -> SessionSnapshotResponse:
        offset = 0
        items: List[MemoryResponse] = []
        while True:
            batch = self.list_memories(session_id=session_id, limit=min(limit, 500), offset=offset)
            if not batch:
                break
            items.extend(batch)
            if len(batch) < min(limit, 500):
                break
            offset += len(batch)
            if len(items) >= limit:
                break
        return SessionSnapshotResponse(
            session_id=session_id,
            exported_at=_now_iso(),
            total=len(items),
            memories=items,
        )

    def restore_session(self, session_id: str, request: SessionRestoreRequest) -> int:
        if request.mode == "replace":
            self.delete_session(session_id)

        count = 0
        for item in request.memories:
            upsert = MemoryUpsert(
                id=item.id,
                external_id=item.external_id,
                content=item.content,
                name=item.name,
                session_id=session_id,
                tags=item.tags,
            )
            self.upsert_memory(upsert)
            count += 1
        return count

    def delete_memory(self, block_id: str) -> None:
        self.collection.delete(ids=[block_id])

    def delete_bulk(self, ids: List[str]) -> None:
        if not ids:
            return
        self.collection.delete(ids=ids)

    def delete_session(self, session_id: str) -> None:
        self.collection.delete(where={"session_id": session_id})
