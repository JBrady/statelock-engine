# StateLock Continuity Layer Architecture

## 1. Executive Summary

The revised interpretation is **correct**:

- **Core Track** should remain the stable memory sidecar runtime.
- **Observability Track** should own conversation-centric capabilities such as ingestion, transcript normalization, working-context construction, telemetry, governance, distillation, and provenance relationships.
- **External adapters** such as OpenClaw integrations, agent runtimes, and CLI helpers should consume existing Core memory APIs and selected Observability context/inspection APIs rather than introducing a new first-class `/gateway/*` subsystem inside Core.

This interpretation matches the repository’s current two-track architecture and current runtime role separation.

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 3-6:
  > Core Track: canonical runtime for memory sidecar operations.
  > Observability Track: subsystem for agent execution state, traceability, and governance.
- [`README.md`](../README.md) lines 3-17:
  > StateLock Engine is a self-hosted memory sidecar API … StateLock handles memory persistence/retrieval. It does not route model calls.
- [`docs/local-stack.md`](../docs/local-stack.md):
  > LiteLLM = model router/switchboard.
  > StateLock = memory/continuity sidecar.
  > StateLock itself remains separate from model routing.

## 2. Current Two-Track Architecture

The repo is explicitly organized around two tracks.

### Core Track

Core is the canonical runtime for:

- memory block storage and retrieval
- `/memories/*` APIs
- insights endpoints
- health/readiness
- Chroma-backed persistence

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 14-24
- [`main.py`](../main.py) lines 20-27
- [`app/core/database.py`](../app/core/database.py) lines 10-20
- [`app/routers/memories.py`](../app/routers/memories.py) lines 29-99
- [`app/routers/insights.py`](../app/routers/insights.py) lines 14-39

### Observability Track

Observability is the isolated subsystem for:

- conversations, turns, spans
- working-context construction
- telemetry and explainability
- governance and auditability
- conversation import/export bundles
- distillation and traceability

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 25-34
- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 36-42
- [`experimental/observability/README.md`](../experimental/observability/README.md) lines 13-20
- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py) lines 42-55

## 3. Role of Core Track

Core’s role is to be the **stable memory sidecar runtime**.

That currently includes:

- memory block storage in Chroma
- CRUD/query/upsert over memory blocks
- session-scoped snapshots and restore
- session/tag/stats insights
- health and readiness

Evidence:

- [`README.md`](../README.md) lines 19-32 list current Core features including:
  - session-scoped memory blocks
  - CRUD and semantic query
  - idempotent upsert
  - session snapshot/restore
  - health endpoints
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 98-166 implement add/upsert
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 167-257 implement query/hybrid query
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 375-421 implement snapshot/restore
- [`app/models/schemas.py`](../app/models/schemas.py) lines 99-146 define snapshot, restore, sessions, tags, and stats response models

Core is **not** currently responsible for:

- normalized transcript ingestion
- archive bundles
- working-context assembly
- gateway routing
- telemetry/governance

Evidence:

- [`examples/real-llm-smoke/README.md`](../examples/real-llm-smoke/README.md) lines 10-15:
  > Core Track does not provide a working-context endpoint, so context assembly is intentionally emulated in the script.
- [`README.md`](../README.md) line 11:
  > It does not route model calls.

## 4. Role of Observability Track

Observability is where the repo already places most conversation-level continuity mechanics.

That includes:

- conversation lifecycle and settings
- conversation import/export bundles
- turn and span modeling
- working-context construction
- telemetry snapshots and explainability
- governance actions
- memory distillation

Evidence:

- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 18-31 create conversations
- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62 implement import/export
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py) lines 16-46 implement working-context build/latest
- [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py) lines 25-132 implement telemetry capture and explainability
- [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py) lines 16-56 implement governance actions/logging
- [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py) lines 16-45 implement memory listing and distillation
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py) lines 135-200 show the actual working-context builder
- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 88-158 show the distillation pipeline

This means the following interpretation is correct:

- conversation ingestion belongs primarily to **Observability**
- transcript normalization belongs primarily to **Observability**
- working-context construction belongs primarily to **Observability**
- execution tracing/telemetry belongs primarily to **Observability**
- governance belongs primarily to **Observability**
- memory distillation belongs primarily to **Observability**
- provenance relationships should be defined first in **Observability**, then projected outward only if needed

## 5. How the Continuity Layer Emerges

The long-term “continuity layer” should be understood as an **emergent composition** of both tracks, not as an immediate rewrite of Core.

Practical interpretation:

- **Core** provides durable memory block storage and retrieval.
- **Observability** provides conversation structure, continuity construction, distillation, provenance, and replay-oriented analysis.
- **Adapters/examples** connect agents to one or both tracks depending on need.

That makes the continuity layer:

1. durable memory in Core,
2. conversation-state and context assembly in Observability,
3. adapter integration at the edge.

This is already how the repo behaves in practice.

Evidence:

- [`examples/agent-memory-loop/README.md`](../examples/agent-memory-loop/README.md) lines 3-11 show Core-only memory-sidecar continuity
- [`examples/real-llm-smoke/README.md`](../examples/real-llm-smoke/README.md) lines 3-8 show Core plus script-side context assembly
- [`experimental/observability/README.md`](../experimental/observability/README.md) lines 13-20 show the richer conversation-continuity mechanics living in Observability

## 6. Adapter Integration Model (OpenClaw, agents)

External integrations should remain **adapter-style consumers** of StateLock capabilities.

### Recommended model

- Use Core memory APIs for save/query/session operations
- Use Observability context APIs when a richer conversation-level context model is needed
- Keep model invocation and routing outside StateLock

### Why

- This matches the current local stack separation:
  - Ollama = local model runtime
  - LiteLLM = model router
  - StateLock = continuity/memory system using LiteLLM

Evidence:

- [`docs/local-stack.md`](../docs/local-stack.md) lines 15-24
- [`docs/local-stack.md`](../docs/local-stack.md) lines 110-119

### OpenClaw-specific recommendation

OpenClaw should continue to start as **example integration and tool contract**, not as a first-class internal gateway module.

Evidence:

- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 36-43 define tool wrappers:
  - `memory.save`
  - `memory.query`
  - `memory.clear_session`
- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md) lines 3-11 define the same surface
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md) lines 5-30 and 42-79 define pre-model/post-model hook contracts
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md) line 98:
  > Cloud escalation remains in agent/router layer; `confidence_low` is only a hint signal.

### Conclusion

The following statement is correct:

> OpenClaw, agents, CLI tools, and example adapters should interact with StateLock through existing memory APIs or Observability context APIs, not through a new `/gateway/*` subsystem.

## 7. Conversation Import Architecture

Conversation import should be treated as an **Observability-first ingestion capability**.

### Why

- Observability already owns conversations, turns, spans, working context, telemetry, and distillation.
- Observability already has import/export bundle support.
- Core’s current data model is memory-block-oriented, not transcript-oriented.

Evidence:

- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62
- [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) lines 71-121 and 124-260
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 98-166 and 375-421

### Recommended structure

Import architecture should initially mean:

1. external export file
2. parser/normalizer
3. normalized conversation bundle
4. Observability import
5. optional distillation into Observability memory
6. optional later projection into Core memory blocks

### Raw archive store classification

The “raw archive store” concept is worth preserving, but it should be classified as:

- **future design track**
- likely owned adjacent to **Observability ingestion**
- not an immediate Core subsystem

Current repo evidence:

- no root `app/importers/`
- no archive tree like `archive/platform/conversation_id/raw.json`
- no current raw archive store implementation

Command evidence:

```text
$ rg -n "archive/|Raw Archive Store|raw.json|normalized.json" .
[no relevant matches]
```

## 8. Provenance and Distillation Model

The right long-term model is:

- imported conversation artifacts
- distilled observations/memory entries
- optional projection into Core memory blocks

Observability already has part of this.

Evidence:

- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 121-123 record:
  - `source_turn_ids_json`
  - `source_span_ids_json`
- [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) lines 244-260 preserve span provenance and relationships on import
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) includes provenance-related JSON fields on spans

### Stable interface to define next: provenance link model

Suggested minimum shape:

```json
{
  "origin_type": "imported|native|distilled",
  "source_platform": "chatgpt|claude|markdown|telegram|discord|whatsapp|manual",
  "conversation_id": "uuid",
  "source_turn_ids": ["..."],
  "source_span_ids": ["..."],
  "observability_memory_id": "uuid|null",
  "core_memory_block_id": "string|null"
}
```

This keeps provenance explicit without forcing Core to own transcript-level history.

## 9. Long-Term Promotion Path (Observability → Core)

Promotion should be **incremental**, preserving subsystem coherence.

That means:

1. keep conversation-centric capabilities isolated under `experimental/observability/`
2. stabilize interfaces and schemas first
3. promote cohesive modules later into a future `app/observability/` namespace
4. do **not** scatter context/import/distillation concerns across root `app/` prematurely

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 44-62 define the post-promotion target structure:
  ```text
  app/
    core/
      memories/
      storage/
      insights/

    observability/
      conversations/
      spans/
      telemetry/
      governance/
  ```
  and state:
  > Promotion is incremental and must preserve subsystem coherence; observability components should not be scattered across unrelated directories.

### Continuity-layer interpretation of promotion

Long term, the continuity layer may become more unified conceptually, but the **promotion path should still respect current ownership**:

- Core remains the durable memory runtime
- Observability becomes the promoted conversation/traceability subsystem
- adapters remain outside the backend core path

## 10. Deferred Design Tracks (crypto, PQC, encrypted archives)

Crypto and PQC should be treated as **deferred design tracks**, not immediate implementation steps.

### Why

- There is no current repo evidence for:
  - AES-at-rest implementation
  - PQC key wrapping
  - signed archive bundles
  - root `app/security/`

Command evidence:

```text
$ rg -n "ML-KEM|ML-DSA|SLH-DSA|AES-256-GCM|wrapped_key|signature.sig|app/security" .
[no relevant matches]
```

### What should be preserved from the earlier proposal

#### Raw archive store

- **Preserve conceptually**
- classify as **future design track**
- likely adjacent to Observability ingestion

#### Distillation pipeline

- **Already exists**
- primarily **belongs to Observability**

Evidence:

- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py)

#### Context builder

- **Already exists**
- primarily **belongs to Observability**

Evidence:

- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py)

#### Gateway adapters

- **Preserve conceptually**
- but classify as **external adapter contract**, not Core backend subsystem

Evidence:

- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md)
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md)

#### Encrypted export bundles

- **Future design track**
- worth documenting later once import/archive formats stabilize

## Near-Term Design Note

Two follow-on design tracks are consistent with this architecture and should remain
Observability-led rather than Core-led:

1. **Experience / procedural memory extraction**
2. **Memory stratification across raw, working, semantic, episodic, and procedural layers**

These are documented in:

- [`docs/statelock-cognitive-architecture.md`](../docs/statelock-cognitive-architecture.md)
- [`docs/architecture-memory-stratification.md`](../docs/architecture-memory-stratification.md)

This note is intentionally short to avoid duplicating the detailed layering and
experience-model discussion in those focused documents.

The corresponding promotion/routing design is documented in:

- [`docs/architecture-promotion-engine.md`](../docs/architecture-promotion-engine.md)
- [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)

## Stable Interfaces To Define Next

### Interface 1: Normalized conversation bundle schema

Purpose:

- unify imported conversation formats before ingestion

Recommended owner:

- Observability

Reason:

- import/export already exists there

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

### Interface 2: Provenance link model

Purpose:

- connect imported conversations, distilled observations, and Core memory blocks

Recommended owner:

- Observability first

Reason:

- it already carries source-turn/source-span lineage

Suggested shape:

```json
{
  "origin_type": "imported|native|distilled",
  "source_platform": "chatgpt|claude|markdown|telegram|discord|whatsapp|manual",
  "conversation_id": "uuid",
  "source_turn_ids": ["..."],
  "source_span_ids": ["..."],
  "observability_memory_id": "uuid|null",
  "core_memory_block_id": "string|null"
}
```

### Interface 3: External adapter contract

Purpose:

- let OpenClaw-style systems consume StateLock capabilities without turning StateLock into a model router

Recommended owner:

- examples/contracts first, later formal docs

Minimal contract:

- memory query
- memory save
- clear session
- optional Observability working-context lookup

This is already close to the current tool contract in:

- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md)
