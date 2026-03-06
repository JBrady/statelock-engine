# StateLock Promotion Schemas and Projection Boundary

## 1. Executive Summary

This schema pass is both **sound** and **necessary**.

The repo’s architecture docs now align on the big picture:

- **Core Track** is the stable memory sidecar runtime.
- **Observability Track** owns conversation-centric continuity, traceability, governance, and distillation.
- **Promotion** should happen primarily in Observability, not in Core.

What is still underspecified is the exact contract between:

- captured artifacts,
- promotion evidence,
- promotion decisions,
- promotion lifecycle state,
- and the narrow projection boundary into Core durable semantic memory blocks.

Repo-aligned conclusion:

- **Observability** should own the rich promotion objects.
- **Core** should receive only a **reduced semantic projection** in the shape of a normal Core memory block.
- The canonical cross-track record should be a **ProjectionRecord** stored on the Observability side and pointing to the Core memory block that was created or updated.

Evidence:

- [`README.md`](../README.md#L3) defines StateLock as a memory sidecar and states it does not route model calls.
- [`docs/architecture-tracks.md`](./architecture-tracks.md#L14) defines Core as the canonical runtime and Observability as the subsystem for traceability and governance.
- [`app/models/schemas.py`](../app/models/schemas.py#L8) shows Core accepts simple memory-block payloads rather than rich provenance-heavy records.
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L16) already contains conversations, turns, spans, working contexts, telemetry snapshots, memory entries, governance events, and pipeline logs.

## 2. Why Schema Precision Is the Next Bottleneck

The architecture is conceptually strong, but implementation planning will stall unless the promotion boundary is explicit.

Without schema precision, several failure modes become likely:

- Core receives overly rich or unstable objects and stops being “narrow and boring”.
- Observability and Core duplicate state without a clear source of truth.
- provenance disappears at the moment of projection.
- contradiction, supersession, and review states are modeled inconsistently.

The repo already shows a clear asymmetry that should be preserved:

- Core memory objects are intentionally simple: content, name, session, tags, timestamps, deterministic IDs via `external_id` ([`app/models/schemas.py`](../app/models/schemas.py#L50), [`app/services/memory_service.py`](../app/services/memory_service.py#L128)).
- Observability objects are intentionally richer and already carry run- and trace-level evidence, contradictions, quarantine fields, counters, and governance logs ([`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L46), [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L95), [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L112)).

That makes schema design at the **promotion boundary** the next bottleneck.

## 3. Current Repo Reality and Existing Relevant Models

### Core models that shape the boundary

Core already has a stable durable-memory contract:

- `MemoryCreate`
- `MemoryUpsert`
- `MemoryResponse`
- `SessionSnapshotResponse`

Evidence:

- [`app/models/schemas.py`](../app/models/schemas.py#L46) defines the Core write payloads.
- [`app/services/memory_service.py`](../app/services/memory_service.py#L98) stores only `content`, `name`, `session_id`, `tags_json`, timestamps, and optional `external_id`.

Important implication:

Core has **no current schema slot** for:

- source conversations,
- turn/span refs,
- evidence sets,
- decision modes,
- review states,
- contradiction refs,
- promotion scores.

Those must remain Observability-owned.

### Observability models that already approximate promotion data

Observability already has several adjacent concepts:

- `Span.provenance_json`
- `Span.contradictions_json`
- `Span.quarantined_until`
- `TelemetrySnapshot.run_group_id`
- `TelemetrySnapshot.metrics_json`
- `TelemetrySnapshot.actions_taken_json`
- `MemoryEntry.memory_type`
- `MemoryEntry.status`
- `MemoryEntry.source_turn_ids_json`
- `MemoryEntry.source_span_ids_json`
- `MemoryEntry.success_count`
- `MemoryEntry.failure_count`

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L46)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L95)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L112)
- [`experimental/observability/app/schemas/models.py`](../experimental/observability/app/schemas/models.py#L125) exposes `memory_type` as `episodic | semantic | procedural`.

Important implication:

The repo already has the building blocks for:

- artifact provenance
- contradiction handling
- quarantine/safety handling
- semantic vs procedural vs episodic classification
- reinforcement/deprecation signals

What it does **not** yet have is a single explicit promotion schema layer tying them together.

### Existing adapter contract

OpenClaw-style integrations already consume a narrow memory contract rather than a gateway API.

Evidence:

- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md#L5) defines `memory.query`.
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md#L42) defines `memory.save`.

Important implication:

The promotion boundary should eventually expose a **narrow adapter contract**, not make external agents speak full internal promotion schemas.

## 4. PromotionArtifact

### Purpose

`PromotionArtifact` is the normalized unit entering the promotion pipeline.

It should live in **Observability**.

It is not a Core object.

### Recommended shape

```yaml
PromotionArtifact:
  artifact_id: string
  artifact_type: string
  source_type: string
  source_platform: string | null
  content: string
  summary: string | null
  conversation_id: string | null
  turn_ids: string[]
  span_ids: string[]
  run_group_id: string | null
  session_id: string | null
  origin_actor: string | null
  created_at: datetime
  metadata: object
  trust_signals: object
  candidate_layers: string[]
```

### Field guidance

- `artifact_id`: keep
- `artifact_type`: keep
- `source_type`: keep
- `source_platform`: optional, useful for imports/adapters
- `content`: keep
- `summary`: optional, do not require in MVP
- `conversation_id`: keep when applicable
- `turn_ids`: keep
- `span_ids`: keep
- `run_id`: **rename to `run_group_id`** to match existing Observability terminology ([`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L101))
- `session_id`: keep, because external adapters and Core already use it ([`app/models/schemas.py`](../app/models/schemas.py#L20))
- `actor`: **rename to `origin_actor`** or `speaker` for clarity; the repo already uses `speaker` on turns ([`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L37))
- `metadata`: keep, but narrow
- `trust_signals`: keep; this aligns with existing trust and alarm concepts
- `candidate_layers`: useful but **future/derived**; it does not need to be stored in the first version

### Repo-aligned interpretation

Implemented now:

- parts of this object are already spread across `Turn`, `Span`, `WorkingContext`, `TelemetrySnapshot`, and `MemoryEntry`

Conceptual/future:

- one normalized `PromotionArtifact` record unifying them

## 5. PromotionEvidence

### Purpose

`PromotionEvidence` explains **why** an artifact deserves promotion or non-promotion.

It should also remain **Observability-owned**.

### Recommended shape

```yaml
PromotionEvidence:
  evidence_id: string
  artifact_id: string
  evidence_type: string
  source_refs:
    conversation_id: string | null
    turn_ids: string[]
    span_ids: string[]
    snapshot_ids: string[]
    governance_event_ids: string[]
  repetition_count: integer
  confidence: float | null
  explicitness: float | null
  correction_signal: float | null
  contradiction_refs: string[]
  notes: string | null
  signals: object
```

### Field guidance

- `source_refs`: keep as structured refs, not opaque text
- `repetition_count`: keep
- `confidence`: keep
- `explicitness`: keep
- `correction_signal`: keep
- `contradiction_refs`: keep
- `notes`: optional only
- `signals`: useful as an extension bucket for metrics not yet stabilized

### Why this fits the repo

This schema maps cleanly onto existing evidence sources:

- `source_turn_ids_json` / `source_span_ids_json` on `MemoryEntry`
- `metrics_json` / `actions_taken_json` on `TelemetrySnapshot`
- `contradictions_json` and `provenance_json` on `Span`
- governance logs on `GovernanceEvent`

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L62)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L108)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L125)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L132)

## 6. PromotionDecision

### Purpose

`PromotionDecision` is the engine’s explicit routing/promotion outcome for an artifact.

### Recommended shape

```yaml
PromotionDecision:
  decision_id: string
  artifact_id: string
  target_layer: string
  decision_outcome: string
  confidence: float | null
  reason_codes: string[]
  evidence_ids: string[]
  decided_by: string
  decision_mode: string
  requires_review: boolean
  created_at: datetime
```

### Terminology guidance

- `decision`: rename to **`decision_outcome`** for clarity
- `decided_by`: keep, but allow values such as:
  - `rule_engine`
  - `heuristic_classifier`
  - `llm_judge`
  - `human_review`
  - `hybrid`
- `decision_mode`: keep, matching the promotion-engine doc:
  - `immediate`
  - `delayed`
  - `aggregated`
  - `human_gated`

### Why it is necessary

The repo currently has actions and heuristics, but not a durable decision record connecting:

- artifact
- evidence
- target layer
- mode
- review requirement

That gap should be closed in Observability before any projection to Core.

## 7. PromotionStatus

### Purpose

`PromotionStatus` separates lifecycle from safety/handling state.

That separation matters because the repo already treats quarantine as a special handling state, not normal progression.

Evidence:

- `Span.quarantined_until` exists independently of memory lifecycles in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L64)
- `MemoryEntry.status` already mixes lifecycle-like and safety-like terms (`active`, `deprecated`, `quarantined`) in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L124)

### Recommended model

```yaml
PromotionStatus:
  lifecycle_state: enum[
    captured,
    candidate,
    promoted,
    reinforced,
    deprecated,
    retired
  ]
  safety_state: enum[
    normal,
    quarantined,
    disputed,
    superseded,
    review_required
  ]
```

### Recommendation

Preserve the earlier design choice:

- **`quarantined` should remain orthogonal to lifecycle**

That keeps the model cleaner and avoids encoding safety as if it were just another maturity stage.

## 8. ProjectionRecord

### Purpose

`ProjectionRecord` is the most important new schema.

It should be the **canonical boundary object** between Observability and Core.

### Recommended shape

```yaml
ProjectionRecord:
  projection_id: string
  source_artifact_id: string
  source_decision_id: string
  source_layer: string
  projection_type: string
  projection_status: string
  projected_at: datetime | null
  projected_by: string
  destination_memory_block_id: string | null
  destination_memory_external_id: string | null
  projection_fidelity: enum[lossy, lossless]
  projection_notes: string | null
  supersedes_memory_block_id: string | null
  provenance_refs:
    conversation_id: string | null
    turn_ids: string[]
    span_ids: string[]
    run_group_id: string | null
    evidence_ids: string[]
    decision_id: string
  core_memory_payload:
    content: string
    name: string | null
    session_id: string
    tags: string[]
    external_id: string
```

### Why this is the canonical boundary object

The boundary should not be the full promoted artifact.

It should not be raw trace records.

It should be:

1. a **Core-compatible semantic projection payload**, plus
1. an **Observability-side trace record** proving where it came from and why it was promoted.

That is exactly what `ProjectionRecord` captures.

### Core payload guidance

Core should receive only the reduced `core_memory_payload`, which is intentionally shaped like `MemoryUpsert`.

Evidence:

- [`app/models/schemas.py`](../app/models/schemas.py#L50) defines `MemoryUpsert` with `id`, `external_id`, `content`, `name`, `session_id`, and `tags`
- [`app/services/memory_service.py`](../app/services/memory_service.py#L128) shows Core already supports deterministic `external_id`-driven upserts

### Important naming recommendation

`lossy_or_lossless` should be renamed to **`projection_fidelity`**.

It is cleaner and easier to type as an enum.

`provenance_bundle` should be replaced by **structured `provenance_refs`** in the first version.

Opaque provenance blobs are harder to reason about and harder to query.

## 9. Observability → Core Projection Boundary

### Canonical answer

The canonical boundary object should be:

- **`ProjectionRecord` in Observability**

And the actual payload sent to Core should be:

- a **reduced semantic projection** compatible with `MemoryUpsert`

### Therefore Core should receive

Not this:

- full promoted artifacts
- full evidence graphs
- run traces
- raw telemetry snapshots
- governance logs

Instead, Core should receive only:

- already-distilled stable semantic memory blocks
- with deterministic IDs and simple retrieval metadata

### Projection direction

Projection should be:

- **one-way operationally**
- **traceable by provenance**
- **reversible by supersession/deprecation**, not by full round-trip reconstruction

That means:

- Core is not the source of truth for promotion history.
- Observability remains the source of truth for why a memory exists and whether it should still be considered valid.

## 10. What Projects Into Core vs What Stays in Observability

### Projects into Core

- stable durable semantic memory
- explicit user preferences that have cleared promotion thresholds
- stable architecture/project facts
- recurring workflow facts once abstracted into semantic form

### Stays in Observability

- raw archive/transcript material
- working memory / active context state
- telemetry snapshots
- governance logs
- contradiction sets
- review queues
- procedural / experience memory
- most episodic memory

### Episodic memory rule

Episodic memory should **not** project directly into Core by default.

If it projects at all, it should first be **transformed** into a durable semantic or policy-level conclusion.

Example:

- episode: “On 2026-03-06, the sessions page falsely showed `Load failed` due to a redirect loop and shared error state.”
- semantic projection: “The Core memories collection route requires canonical trailing-slash handling through the proxy.”

### Procedural / experience memory rule

Procedural / experience memory should remain Observability-owned.

Schema-level difference from durable semantic memory:

- semantic memory answers **what is true / stable**
- procedural / experience memory answers **what tends to work / fail**

The latter is closer to telemetry- and outcome-conditioned heuristics than to durable fact memory.

### Policy / constraints rule

Policy / constraints items should generally **not** project into Core as ordinary memory.

They should live in:

- docs
- config
- explicit runtime constraints
- governance/policy registries

An exception may exist for user-authored explicit preferences that are intentionally modeled as durable semantic memory, but that should be a deliberate special case.

## 11. Provenance Requirements

Minimum provenance that must survive projection:

- source artifact id
- source decision id
- source conversation id when present
- source turn/span refs when present
- source run group id when present
- destination Core memory block id
- destination deterministic external id
- projection timestamp
- supersession pointer when applicable

Why:

Without these, Core memory becomes detached from:

- the conversation/run that produced it
- the decision/evidence that justified promotion
- later contradiction or retirement logic

This is especially important because Core storage itself does not currently carry rich provenance fields.

## 12. Contradiction / Supersession / Review Handling

### Contradiction

Contradiction should be modeled primarily in Observability, not in Core.

Use:

- contradiction refs in `PromotionEvidence`
- `disputed` or `review_required` safety state in `PromotionStatus`

Core should not need native contradiction machinery in the first version.

### Supersession

Supersession should be modeled through:

- `supersedes_memory_block_id` on `ProjectionRecord`
- `safety_state = superseded` on prior decision/projection records
- optional deprecation of related Observability memory entries

This preserves a clean chain without forcing Core to support lineage graphs.

### Review handling

Human approval should fit without overcomplicating v1:

- `requires_review: boolean` on `PromotionDecision`
- `safety_state = review_required` on `PromotionStatus`
- optional `reviewed_by`, `reviewed_at`, `review_notes` can be deferred until actual UI/workflow design exists

That keeps the first schema implementation-friendly.

## 13. Minimal Viable Schema Set

Recommended minimum schema set for the first implementation phase:

1. `PromotionArtifact`
1. `PromotionEvidence`
1. `PromotionDecision`
1. `ProjectionRecord`

`PromotionStatus` can be implemented either:

- as a small embedded subobject on artifact/decision records, or
- as a separate table/model later if lifecycle transitions become complex

Why this is enough:

- artifact = what entered the pipeline
- evidence = why promotion seems justified
- decision = what the engine decided
- projection = what crossed into Core

That is the minimum needed for auditable promotion.

## 14. Recommended Implementation Sequence

1. **Document the schema boundary first**
   - this document
1. **Add Observability-side conceptual models**
   - artifact, evidence, decision, projection
1. **Keep Core unchanged initially**
   - reuse `MemoryUpsert` payload shape
1. **Add projection write path**
   - Observability emits reduced semantic block into Core
1. **Add reinforcement/deprecation hooks**
   - driven by telemetry/governance outcomes
1. **Only then consider richer review/supersession UI**

This sequence keeps Core stable and pushes experimentation where the repo already expects it: Observability.

## 15. Open Questions

1. Should `PromotionArtifact` be a durable DB model or a normalized transient pipeline object first?
1. Should `PromotionEvidence` be one record per source signal, or a compact aggregate per decision?
1. What deterministic `external_id` strategy should be used for projected Core blocks?
1. When an existing Core block is superseded, should Core memory content be updated in place or appended as a new block with lineage kept only in Observability?
1. Should some high-confidence explicit user constraints bypass the normal semantic projection path and land in a separate policy registry instead of Core memory?

## Cross-Reference

- Promotion/routing behavior: [`docs/architecture-promotion-engine.md`](./architecture-promotion-engine.md)
- Layering model: [`docs/architecture-memory-stratification.md`](./architecture-memory-stratification.md)
- Relationship/provenance structure: [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)
- Track ownership: [`docs/architecture-continuity-layer.md`](./architecture-continuity-layer.md)
