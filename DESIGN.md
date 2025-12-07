# StateLock Engine - Design Document

## 1. Overview & Vision
The StateLock Engine was originally designed to extend LLM context windows. In the current AI landscape (post-2023/2024), the focus shifts from raw *context extension* to **Structured State Management for Agents**.

**Core Value Proposition:**
- **State Persistence:** Agents need to remember things across runs (User preferences, learned facts).
- **Noise Reduction:** Even with 1M token windows, retrieving *only* the relevant facts reduces cost, latency, and hallucination.
- **Namespace Isolation:** Multi-tenant or multi-agent systems need isolated memory buckets (Sessions).

## 2. Architecture Refactor

### Current State
- Monolithic `main.py`.
- Hardcoded dependency on local `sentence-transformers`.
- Flat memory structure (everything in one collection).
- No testing.

### Proposed Architecture

The application will be refactored into a modular Python package structure:

```
app/
├── core/           # Configuration, Database setup, Logging
│   ├── config.py
│   └── database.py
├── routers/        # FastAPI Routes
│   ├── memories.py
│   └── health.py
├── services/       # Business Logic
│   ├── memory_store.py    # CRUD + Search logic
│   └── embedder.py        # Abstracted embedding interface
├── models/         # Pydantic Schemas
│   └── schemas.py
└── main.py         # Entry point
```

## 3. Key Feature Upgrades

### A. Sessions (Namespacing)
Instead of a single global bucket of memories, every memory belongs to a `session_id`.
- **Use Case:** Separate memory for "User A" vs "User B", or "Agent Run 101".
- **Implementation:** Metadata field `session_id` in ChromaDB, used as a filter during query/retrieval.

### B. Richer Metadata
Memories should have:
- `created_at` (Timestamp)
- `updated_at` (Timestamp)
- `tags` (List[str] - e.g., ["fact", "preference"])
- `metadata` (JSON blob for arbitrary extra data)

### C. Modular Embeddings
Support swapping the embedding provider.
- **Interface:** `EmbeddingProvider` abstract base class.
- **Implementations:** `LocalHuggingFace` (default), `OpenAI` (optional, via API key).

## 4. API Specification (Draft)

- `POST /memories/` - Create a memory (requires `content`, optional `session_id`, `tags`).
- `POST /memories/search` - Semantic search (requires `query`, optional `session_id` filter).
- `GET /memories/{memory_id}` - Get details.
- `DELETE /memories/{memory_id}` - Delete.
- `DELETE /sessions/{session_id}` - Clear all memories for a session.

## 5. Technology Stack
- **Framework:** FastAPI (unchanged)
- **Database:** ChromaDB (unchanged, but better utilized)
- **Config:** `pydantic-settings` for robust env var handling.
- **Testing:** `pytest`
