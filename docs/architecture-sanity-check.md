# Architecture Sanity Check

## 1. Executive Summary

The proposed architecture is **directionally useful as a long-range product vision**, but it is **not accurate as the immediate architecture plan for this repo without revision**.

The most important correction is structural:

- **Core Track** is currently a memory sidecar runtime, not a model gateway.
- **Observability Track** already owns most of the conversation-level concepts in the proposal: conversation import/export, working-context construction, telemetry, governance, and memory distillation.
- **OpenClaw integration** is currently documented and implemented as an external tool/sidecar contract, not as first-class `/gateway/*` routes inside Core.
- **Encrypted local storage / PQC** is not evidenced as current repo groundwork and should be treated as a future security design track, not part of the near-term MVP.

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md): “Core Track: canonical runtime for memory sidecar operations” and “Observability Track: subsystem for agent execution state, traceability, and governance.” See lines 3-6 and 14-34.
- [`README.md`](../README.md): “StateLock handles memory persistence/retrieval. It does **not** route model calls.” See lines 3-17.
- [`experimental/observability/README.md`](../experimental/observability/README.md): Observability already “builds bounded working context,” “computes telemetry,” and “distills long conversations into reusable memory entries.” See lines 13-20.

Bottom line:

- The proposal should be **revised** before implementation.
- The safest path is to keep **Core stable**, keep new conversation-centric capabilities in **Observability**, and start any OpenClaw work as **examples/adapters first**, not as a new root gateway subsystem.

## 2. Current Repo Reality

### 2.1 Core Track today

Core is a FastAPI memory sidecar with Chroma-backed storage and a narrow runtime role.

Evidence:

- [`README.md`](../README.md) lines 3-17:
  > StateLock Engine is a self-hosted memory sidecar API … StateLock handles memory persistence/retrieval. It does not route model calls.
- [`main.py`](../main.py) lines 20-27:
  ```python
  app = FastAPI(...)
  app.include_router(memories.router, prefix=settings.API_PREFIX, tags=["Memories"])
  app.include_router(insights.router, tags=["Insights"])
  ```
- [`app/core/config.py`](../app/core/config.py) lines 10-21:
  ```python
  API_PREFIX: str = "/memories"
  AUTH_REQUIRED: bool = False
  STATELOCK_API_KEY: str = ""
  ```
- [`app/core/database.py`](../app/core/database.py) lines 10-20:
  ```python
  cls._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
  cls._collection = client.get_or_create_collection(name="memory_blocks")
  ```
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 98-166 and 167-257 show add/upsert/query/hybrid query over memory blocks, not transcript ingestion or provenance archives.

Core endpoints confirmed in repo:

- [`app/routers/memories.py`](../app/routers/memories.py) lines 29-99
- [`app/routers/insights.py`](../app/routers/insights.py) lines 14-39
- [`main.py`](../main.py) lines 92-104

These cover:

- `POST /memories/`
- `POST /memories/upsert`
- `POST /memories/query`
- `POST /memories/query-hybrid`
- `GET /memories/`
- session snapshot/restore
- `/stats/overview`
- `/sessions`
- `/tags`
- `/healthz`
- `/readyz`

### 2.2 Observability Track today

Observability is already a substantial conversation-centric subsystem under `experimental/observability/`.

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 25-34 assigns Observability:
  - conversations, turns, spans
  - working context construction
  - execution telemetry and explainability
  - governance actions and auditability
  - conversation export/import bundles
- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py) lines 42-55 mounts routers for:
  - conversations
  - turns
  - segmentation
  - context
  - telemetry
  - governance
  - memory
  - spans
  - debug
- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62 already implements:
  - `POST /v2/conversations/import`
  - `GET /v2/conversations/{conversation_id}/export`
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py) lines 16-46 already implements:
  - `POST /v2/conversations/{conversation_id}/working_context`
  - `GET /v2/conversations/{conversation_id}/working_context/latest`
- [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py) lines 16-45 already implements:
  - `GET /v2/memory`
  - `POST /v2/conversations/{conversation_id}/memory/distill`

### 2.3 Current OpenClaw integration model

OpenClaw is currently integrated in **sidecar/tool mode**, not via internal gateway routes.

Evidence:

- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 36-43:
  > Use a tool wrapper that calls StateLock:
  >
  > - `memory.save`
  > - `memory.query`
  > - `memory.clear_session`
- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 66-75 show the current flow:
  1. Agent receives message
  1. derive session id
  1. call `memory.query`
  1. build prompt
  1. call LiteLLM
  1. save facts with `memory.save`
- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md) lines 3-11 defines the tool surface:
  - `memory.save`
  - `memory.query`
  - `memory.clear_session`

### 2.4 Web UI role today

The Next app is a **thin proxy UI**, not an orchestration or gateway layer.

Evidence:

- [`apps/web/README.md`](../apps/web/README.md) lines 1-4:
  > Thin Next.js UI for the existing Core and Observability backends.
- [`apps/web/README.md`](../apps/web/README.md) lines 18-20:
  - `/api/core/*`
  - `/api/obs/*`
- [`apps/web/lib/proxy.ts`](../apps/web/lib/proxy.ts) lines 40-55 and 171-189 show env-pinned upstream proxying, not business logic ownership.

## 3. Proposed Architecture vs Current Repo Matrix

| Proposed subsystem | Repo status | Evidence | Notes |
|---|---|---|---|
| `app/importers/` historical chat importers | **Missing in root app** | `find app -maxdepth 2 -type d | sort` returns only `app/core`, `app/models`, `app/routers`, `app/services` | Import-like behavior exists only as conversation bundle import in Observability, not root Core importers. |
| normalized conversation schema | **Partially exists** | [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) lines 71-121 and 124-260 | Exists as Observability conversation bundle schema, not as a cross-platform chat-import schema for ChatGPT/Claude/Telegram/Discord. |
| raw archive store of exact originals | **Missing** | `rg -n "archive/|Raw Archive Store|raw.json|normalized.json" .` returned no relevant hits | No repo evidence of filesystem raw transcript archive storage. |
| provenance/audit/replay | **Partially exists** | [`docs/provenance/seed-migration-manifest.md`](../docs/provenance/seed-migration-manifest.md), [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) | Provenance exists in limited forms, but not the proposed raw-archive-backed provenance tracker. |
| memory distiller | **Exists in Observability, not Core** | [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 88-158 | The repo already has a distillation engine, but it belongs to Observability. |
| distilled memory graph/vector DB | **Partially exists** | Core uses Chroma memory blocks in [`app/core/database.py`](../app/core/database.py); Observability stores `MemoryEntry` records in SQLite via [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py) | There is no explicit “memory graph” subsystem. Current storage is split across Core Chroma and Observability SQLite memory entries. |
| context builder / rehydration engine | **Exists in Observability, not Core** | [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py) lines 135-200; [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py) lines 16-46 | Core examples emulate context assembly in scripts instead of owning a context-builder API. |
| gateway adapter inside StateLock | **Conflicts with current design** | [`README.md`](../README.md) lines 11-17; [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 36-75 | Current architecture says StateLock is a memory sidecar and OpenClaw owns agent/model flow. |
| `/gateway/context`, `/gateway/memory`, `/gateway/session/*` endpoints | **Missing and inconsistent with current API shape** | `rg -n "/gateway/|gateway" .` finds docs references but no runtime routes | Current API nouns are `/memories/*`, `/sessions`, `/tags`, and `/v2/conversations/*`; `/gateway/*` would be a new design surface. |
| encrypted local storage model with PQC | **Speculative / missing** | `rg -n "ML-KEM|ML-DSA|SLH-DSA|AES-256-GCM|wrapped_key|signature.sig|app/security" .` returned no relevant hits | No current repo evidence for this as an implementation-ready subsystem. |
| `app/security/` | **Missing** | `find app -maxdepth 2 -type d | sort` | No root security module exists. |

Command output evidence for root app layout:

```text
$ find app -maxdepth 2 -type d | sort
app
app/core
app/models
app/routers
app/services
```

Command output evidence for Observability app layout:

```text
$ find experimental/observability/app -maxdepth 2 -type d | sort
experimental/observability/app
experimental/observability/app/api
experimental/observability/app/context_builder
experimental/observability/app/db
experimental/observability/app/governance
experimental/observability/app/memory
experimental/observability/app/pipelines
experimental/observability/app/schemas
experimental/observability/app/services
experimental/observability/app/telemetry
...
```

## 4. Confirmed Reusable Building Blocks

These pieces are already real and reusable.

### 4.1 Core reusable blocks

- **Chroma-backed memory store** via [`app/core/database.py`](../app/core/database.py) lines 10-20
- **Memory CRUD/query/upsert** via [`app/services/memory_service.py`](../app/services/memory_service.py)
- **Session snapshot/restore** via [`app/services/memory_service.py`](../app/services/memory_service.py) lines 375-421 and [`app/routers/memories.py`](../app/routers/memories.py) lines 78-94
- **Session-id conventions and save policy helpers** via [`app/services/automation_policy.py`](../app/services/automation_policy.py) lines 17-28 and 31-58
- **Current schema contracts** via [`app/models/schemas.py`](../app/models/schemas.py)

### 4.2 Observability reusable blocks

- **Conversation export/import bundle** via [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) and [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py)
- **Working-context builder** via [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py)
- **Memory distillation** via [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py)
- **Turns/spans/telemetry/governance** via [`experimental/observability/app/main.py`](../experimental/observability/app/main.py) and subrouters

### 4.3 Examples and integration assets

- **OpenClaw tool-side integration** via [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md)
- **Core-only working-context emulation** via [`examples/real-llm-smoke/README.md`](../examples/real-llm-smoke/README.md) lines 10-15:
  > Core Track does not provide a working-context endpoint, so context assembly is intentionally emulated in the script.
- **Core-only agent loop** via [`examples/agent-memory-loop/README.md`](../examples/agent-memory-loop/README.md) lines 13-18:
  > Core Track only (`/memories/*` endpoints). No observability integration.

## 5. Incorrect Assumptions or Risky Assumptions

### 5.1 “StateLock sits between OpenClaw and the model API”

This is the biggest architectural mismatch.

Repo reality:

- [`README.md`](../README.md) line 11 says StateLock handles memory persistence/retrieval and “does not route model calls.”
- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 3-10 and 36-75 keep Ollama/LiteLLM/OpenClaw/StateLock as separate concerns.

Conclusion:

- Treating StateLock as a first-class model gateway is **not a minimal extension**. It is a product-direction change.

### 5.2 “New root subsystems can be added with minimal disruption”

This is only partly true.

Safe additions:

- docs
- examples
- scripts
- additive Observability modules

Riskier additions:

- new conversation-centric modules under root `app/`
- new `/gateway/*` routes that re-scope Core

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 44-62 explicitly say post-promotion Observability should remain coherent and not be scattered across unrelated directories.

### 5.3 “No required changes to `memory_service.py`, Chroma integration, existing endpoints”

This is too strong.

Why:

- Current Core `MemoryService` is shaped around **memory blocks**, not conversation archives, transcript provenance, or gateway sessions.
- If the repo adds raw archives, imported turns, provenance links, or gateway packet generation, those need new ownership, schemas, and likely new storage backends.

Evidence:

- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 98-166 are about individual memory blocks.
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 375-421 export/restore **session memory blocks**, not conversation archives.

### 5.4 “Context Builder” belongs in Core right now

Current repo evidence says the opposite.

- Observability owns working-context construction in [`docs/architecture-tracks.md`](../docs/architecture-tracks.md#L25).
- Core examples explicitly emulate context assembly client-side because Core does not expose that surface yet in [`examples/real-llm-smoke/README.md`](../examples/real-llm-smoke/README.md#L10).

Conclusion:

- A root-Core `app/context_builder/` is not the lowest-risk first move.

### 5.5 Proposed crypto/PQC is implementation-ready

This is unsupported by current repo evidence.

Command evidence:

```text
$ rg -n "ML-KEM|ML-DSA|SLH-DSA|AES-256-GCM|wrapped_key|signature.sig|app/security" .
[no relevant matches]
```

Conclusion:

- Crypto design should be treated as **future / speculative**, not “next subsystem to add.”

## 6. OpenClaw / Gateway Integration Recommendation

### Recommendation

Start OpenClaw integration as an **example integration / adapter contract**, not as a first-class gateway module inside Core.

### Why

- This matches the repo’s current role separation.
- It preserves the current “StateLock is a memory sidecar” contract.
- It allows incremental adoption without committing Core to model-routing responsibilities.

Evidence:

- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md) lines 3-11 already define a minimal tool surface.
- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 36-75 already document the current operational flow.

### Minimal API surface StateLock should expose first

For OpenClaw, the lowest-risk first-class surfaces are probably:

1. **Keep existing Core memory APIs**
   - `POST /memories/`
   - `POST /memories/query`
   - `POST /memories/query-hybrid`
   - session snapshot/restore
1. **Optionally reuse Observability working-context API experimentally**
   - `POST /v2/conversations/{conversation_id}/working_context`
1. **Do not add `/gateway/*` yet**

### Endpoint naming fit

`/gateway/context` and `/gateway/memory` do **not** match the current API shape well.

Current repo naming is resource-oriented:

- Core: `/memories/*`, `/sessions`, `/tags`
- Observability: `/v2/conversations/*`, `/v2/.../working_context`, `/v2/.../telemetry`

If a future adapter API is needed, a more consistent fit would be:

- keep it outside Core as example/tool code first
- or, if eventually promoted, model it around existing nouns rather than a generic `/gateway/*` umbrella

## 7. Import Pipeline Recommendation

### Recommendation

Treat historical import as an **Observability-first ingestion subsystem**, not as an immediate root-Core feature.

### Why

- Conversation import/export already exists in Observability.
- Observability already owns turns, spans, working context, distillation, and replay-adjacent portability.
- Historical imports are conversation-centric, not just memory-block-centric.

Evidence:

- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62
- [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) lines 71-121 and 124-260

### Recommended first scope

1. Define a **normalized conversation bundle schema** compatible with Observability import/export.
1. Add importer/parser modules under **Observability** or a dedicated ingestion package adjacent to it.
1. Keep raw archive storage additive and explicit.
1. Only later decide whether distilled outputs should be projected into Core memory blocks.

### Should raw archive store + distilled memory graph + context builder be treated as…

- **raw archive store**: separate ingestion subsystem
- **distilled memory**: background or offline pipeline, initially Observability-owned
- **context builder**: existing Observability runtime component

So the best classification is:

- **separate ingestion subsystem + background pipeline**, not a simple extension of Core runtime.

## 8. Encrypted Storage / PQC Recommendation

### Recommendation

Defer PQC and broad encrypted-storage architecture from the first implementation wave.

### What is realistic now

Near-term, low-risk options would be:

- document security boundaries
- define export-bundle integrity requirements
- isolate where raw archives or export bundles would live on disk

### What should be deferred

- ML-KEM wrapped keys
- ML-DSA or SLH-DSA signed bundles
- full encrypted SQLite/raw archive/blob architecture
- introducing a new `app/security/` subsystem before the import/archive model exists

### Why

- There is no current storage-crypto subsystem to extend.
- Adding crypto boundaries before storage ownership is settled usually creates churn.

Command evidence:

```text
$ rg -n "ML-KEM|ML-DSA|SLH-DSA|AES-256-GCM|wrapped_key|signature.sig|app/security" .
[no relevant matches]
```

### Lowest-risk crypto boundary to introduce later

If/when raw archives or export bundles become real, introduce crypto at the **bundle/archive boundary** first, not inside Core Chroma operations.

## 9. Recommended Stable Interfaces to Define First

These are the three most useful interfaces to define first.

### 9.1 Normalized Conversation Bundle Interface

Owner recommendation:

- **Observability**

Reason:

- It already has `Conversation`, `Turn`, `Span`, `Thread`, `TelemetrySnapshot`, and `MemoryEntry` import/export machinery.

Starting shape:

```json
{
  "bundle_version": "statelock_bundle_v1",
  "source_platform": "chatgpt|claude|markdown|telegram|discord|whatsapp",
  "conversation": {
    "external_id": "string",
    "title": "string",
    "created_at": "iso8601"
  },
  "turns": [
    {
      "turn_id": "string",
      "speaker": "user|assistant|system|tool",
      "text": "string",
      "created_at": "iso8601",
      "metadata": {}
    }
  ]
}
```

### 9.2 External Adapter Contract for Agent Runtimes

Owner recommendation:

- **examples/** first, not Core runtime

Reason:

- This matches current OpenClaw sidecar/tool integration.

Suggested initial contract:

- query context from existing memory endpoints
- optionally save memory blocks
- keep model invocation outside StateLock

This can stay as:

- `memory.query`
- `memory.save`
- `memory.clear_session`

before any first-class gateway route is introduced.

### 9.3 Provenance Link Interface Between Imported Conversations and Distilled Memory

Owner recommendation:

- **Observability**

Reason:

- Distillation and import/export already live there.

Suggested minimum fields:

```json
{
  "memory_id": "uuid",
  "conversation_id": "uuid",
  "source_turn_ids": ["..."],
  "source_span_ids": ["..."],
  "origin_type": "imported|native|distilled",
  "import_source": "chatgpt_export|claude_export|markdown|manual"
}
```

This is compatible with current Observability distillation, which already records `source_turn_ids_json` and `source_span_ids_json` in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L121).

## 10. Lowest-Risk Implementation Sequence

1. **Docs/ADR first**
   - revise the proposed architecture so it respects the Core/Observability split
   - explicitly classify gateway, import, and crypto as separate concerns
1. **Observability import schema**
   - formalize normalized conversation bundle format
   - keep this under `experimental/observability/`
1. **Example importers**
   - implement one or two importers as experimental tooling
   - likely ChatGPT export + markdown first
1. **Observability provenance/distillation linkage**
   - make imported turns/spans/distilled memory relationships explicit
1. **OpenClaw adapter examples**
   - extend `examples/openclaw-tooling/`
   - optionally add example use of Observability working-context APIs
1. **Evaluate promotion**
   - only after interfaces settle, decide whether to promote import/distillation pieces out of `experimental/`
1. **Deferred security layer**
   - design encrypted bundles / signing only after archive/export formats stabilize

## 11. File/Module Placement Recommendations

### Put under `app/`

Only if it is clearly Core memory-sidecar functionality:

- additive memory-block APIs
- Core insights
- auth/config/runtime concerns directly tied to Core

### Put under `experimental/`

Recommended placement for now:

- historical conversation importers
- normalized conversation bundle schema
- raw conversation archive handling
- provenance tracker for imported conversations
- conversation-level distillation extensions
- context-builder evolution
- replay/export/import work

Reason:

- This preserves the current two-track model and matches existing responsibilities in [`docs/architecture-tracks.md`](../docs/architecture-tracks.md#L14).

### Put under `apps/web`

Only UI support code:

- inspection UIs for import bundles, replay, or provenance views
- no backend business logic

Evidence:

- [`apps/web/README.md`](../apps/web/README.md) calls the Next app a thin UI.
- [`apps/web/lib/proxy.ts`](../apps/web/lib/proxy.ts) only proxies to env-pinned upstreams.

### Put under `scripts/`

Good fit for:

- one-off importer CLIs
- archive bundle transforms
- migration/validation helpers

### Put under `docs/`

Good fit for:

- import bundle schema docs
- gateway adapter contract docs
- security ADRs for encrypted archive/export design

## 12. Outstanding Questions or Decision Points

1. Should imported conversation data remain purely Observability-owned, or should there be a later projection path into Core memory blocks?
1. Is the long-term goal still to keep StateLock out of model routing entirely, or is there a deliberate future plan to make it a gateway/service mesh component?
1. If chat importers are added, is the first desired output:
   - replay/debugging,
   - memory distillation,
   - or both?
1. Does raw archive storage need to be a filesystem tree, or can the first version rely on versioned portable bundles plus DB-backed normalized records?
1. If crypto is added later, what is the first protected boundary:
   - export bundle,
   - raw archive,
   - or full local DB?
