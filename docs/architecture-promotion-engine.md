# StateLock Promotion Engine

## Executive Summary

The **Promotion Engine** concept is sound and fits the current repository, as long as it is placed primarily in the **Observability Track** and not treated as a Core runtime rewrite.

Repo-aligned interpretation:

- **Observability** should own artifact capture, provenance, classification, scoring, candidate records, experience extraction, and promotion logs.
- **Core** should remain the stable destination for only the narrowest promoted subset: durable semantic memory blocks that are worth persisting in the canonical sidecar runtime.

This matches the existing split:

- Core = durable memory sidecar
- Observability = conversation, context, telemetry, governance, distillation, and traceability

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 14-34 define the Core vs Observability responsibility split.
- [`README.md`](../README.md) lines 3-17 define StateLock as a memory sidecar that does not route model calls.
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 16-151 already model the artifact types and outcome signals a Promotion Engine would need.
- [`docs/architecture-memory-stratification.md`](../docs/architecture-memory-stratification.md) already places raw/working/episodic/procedural layers primarily under Observability.

For the schema contract between Observability promotion records and Core memory blocks, see:

- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)

For profile-driven budget and aggressiveness presets that shape promotion behavior, see:

- [`docs/architecture-memory-policy-profiles.md`](./architecture-memory-policy-profiles.md)

## What the Promotion Engine Is

The Promotion Engine is the subsystem that decides how captured artifacts move through the stratified memory system.

It decides whether an artifact remains:

- archive-only
- working-memory-only
- candidate memory
- durable semantic memory
- episodic memory
- procedural / experience memory
- policy / constraints record

Core principle:

**Capture broadly. Promote narrowly.**

That principle is already consistent with the repo’s current behavior:

- Observability captures rich conversation/run structure.
- Core stores only a simpler durable memory representation.

## Why It Is Necessary

Without a Promotion Engine, StateLock risks collapsing into one of two bad modes:

1. **Everything becomes memory**
   - low-trust or temporary artifacts pollute durable retrieval
1. **Nothing becomes memory**
   - continuity remains trapped in transient traces and never becomes reusable

The repo already hints at the right balance:

- Core uses narrow memory-save semantics and policy helpers in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L31)
- Observability already models distillation, telemetry, governance, provenance, and evaluation-like counters in:
  - [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L88)
  - [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py#L63)
  - [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L29)
  - [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L112)

The Promotion Engine is the missing conceptual layer that ties those existing pieces together.

## Recommended Terminology

Recommended primary term:

- **Promotion Engine**

Recommended secondary phrase:

- **memory promotion pipeline**

Why:

- “Promotion Engine” matches the state-transition nature of the system.
- “memory promotion pipeline” is a useful descriptive alias for docs and design discussions.

Less preferred:

- **routing engine**
  - too broad; could be confused with model routing, which StateLock does not own
- **memory governor**
  - suggests primarily restriction/policing rather than classification and advancement

## Promotion Pipeline

Recommended pipeline:

1. **Artifact normalization**
1. **Artifact classification**
1. **Artifact scoring**
1. **Rule evaluation**
1. **Promotion decision / state transition**
1. **Reinforcement / deprecation / retirement over time**

### 1. Artifact normalization

Purpose:

- turn conversation events, tool outputs, imported bundles, and observed outcomes into a common internal artifact shape

Likely owner:

- Observability

Existing grounding:

- conversation import/export bundle machinery in [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py#L71)
- spans, turns, working contexts, and telemetry snapshots in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L31)

### 2. Artifact classification

Purpose:

- decide whether an artifact is better treated as semantic, episodic, procedural/experience, policy/constraints, or archive-only

Existing grounding:

- `MemoryEntryOut.memory_type` already distinguishes `episodic`, `semantic`, and `procedural` in [`experimental/observability/app/schemas/models.py`](../experimental/observability/app/schemas/models.py#L125)
- current distillation already creates `semantic` and `procedural` entries in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L106)

### 3. Artifact scoring

Purpose:

- estimate whether the artifact deserves promotion, delay, aggregation, or rejection

Existing grounding:

- Observability already scores spans and telemetry influence with deterministic logic in:
  - [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L58)
  - [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py#L45)

### 4. Rule evaluation

Purpose:

- apply deterministic constraints, safety boundaries, explicit user instructions, and trust/policy rules

Existing grounding:

- Core save-policy rules in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)
- governance actions and quarantine behavior in [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L47)

### 5. Promotion decision / state transition

Purpose:

- move artifacts into explicit lifecycle states rather than treating promotion as a hidden side effect

This is mostly conceptual today.

### 6. Reinforcement / deprecation / retirement

Purpose:

- allow memory to strengthen, weaken, or age out based on repeated success, contradiction, obsolescence, or policy risk

Existing grounding:

- `success_count`, `failure_count`, `last_applied_at` in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L127)
- `status` values `active`, `deprecated`, `quarantined` in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L124)
- contradiction and deprecation behavior in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L129)

## Scoring Model

Suggested scoring axes:

- durability
- generality
- specificity
- actionability
- confidence
- repetition
- user-explicitness
- correction-signal
- policy-risk
- retrieval-value

Repo alignment:

- These should be treated as a **conceptual scoring framework**, not current implemented fields.
- The repo currently has pieces of this spread across telemetry metrics, trust scores, memory strength, and save heuristics.

Examples of existing nearby signals:

- trust and recency in spans via [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L58)
- alarms and off-thread coupling in [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py#L45)
- explicit memory-save triggers in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)
- success/failure counters in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L127)

Recommended interpretation:

- **implemented now**: trust, recency, alarms, memory strength, success/failure counters, save-trigger heuristics
- **future**: unified promotion-scoring model that combines them

## Promotion State Machine

Suggested lifecycle states:

- `captured`
- `candidate`
- `promoted`
- `reinforced`
- `deprecated`
- `retired`

Repo alignment:

- `captured`, `candidate`, `promoted`, `reinforced`, and `retired` are **conceptual**
- `deprecated` has a strong precedent already
- `quarantined` already exists and should likely remain alongside this state machine as a safety-oriented status

Evidence:

- existing memory `status` values include `active`, `deprecated`, `quarantined` in [`experimental/observability/app/schemas/models.py`](../experimental/observability/app/schemas/models.py#L125)
- distillation already deprecates outdated procedural memory in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L134)
- governance already quarantines spans in [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L47)

Suggested repo-aligned state model:

```text
captured -> candidate -> promoted -> reinforced
                           |            |
                           v            v
                      deprecated    deprecated
                           |
                           v
                        retired

quarantined = orthogonal safety status, not pure lifecycle state
```

## Decision Modes

Recommended decision modes:

- **immediate promotion**
- **delayed promotion**
- **aggregated promotion**
- **human-gated promotion**

### Immediate promotion

Use when:

- explicit user instruction
- explicit policy statement
- high-confidence stable semantic fact with low policy risk

Current precedent:

- explicit commands and rule triggers in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L31)

### Delayed promotion

Use when:

- artifact may matter, but needs more context or repeated confirmation

Good fit for:

- episodic memories
- uncertain semantic claims

### Aggregated promotion

Use when:

- one artifact alone is weak, but repeated observations strongly imply a stable lesson

Good fit for:

- workflow preferences
- tool reliability patterns
- recurring strategy success/failure

### Human-gated promotion

Use when:

- policy risk is high
- the artifact changes identity, durable constraints, or architecture canon

Good fit for:

- project architectural rules
- user identity updates
- cross-project workflow canon

## Anti-Poisoning Protections

The Promotion Engine should explicitly defend against memory poisoning, self-reinforcing hallucination, and accidental policy drift.

Recommended protections:

1. **Provenance requirement**
   - promoted artifacts must point back to source turns/spans/import records
1. **Contradiction-aware promotion**
   - contradiction with existing durable memory lowers promotion confidence
1. **Quarantine path**
   - suspicious artifacts should be held or quarantined instead of promoted
1. **Policy-risk gating**
   - policy/constraints-like artifacts should require deterministic rules or confirmation
1. **No sole LLM authority**
   - the active conversation model can propose candidates, but not unilaterally promote them

Repo grounding:

- provenance fields exist on spans and memory entries in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L61) and [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L125)
- contradiction links already exist on spans in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L63)
- quarantine already exists in governance flows in [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L47)

## Contradiction, Reinforcement, Deprecation, and Retirement

### Contradiction

Conceptual rule:

- contradiction does not immediately delete memory
- it should reduce confidence or route an artifact to candidate/quarantine review

Repo evidence:

- contradiction links exist on spans in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L63)
- distillation already marks outdated procedural entries as deprecated in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L134)

### Reinforcement

Conceptual rule:

- repeated successful reuse should strengthen promotion confidence and retrieval priority

Repo evidence:

- `success_count` and `last_applied_at` already exist on memory entries in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L127)

### Deprecation

Conceptual rule:

- outdated but historically meaningful artifacts should become less active before full retirement

Repo evidence:

- `deprecated` already exists as a memory status in [`experimental/observability/app/schemas/models.py`](../experimental/observability/app/schemas/models.py#L125)

### Retirement

Conceptual rule:

- stale, contradicted, or low-value artifacts can eventually be retired from active retrieval while still preserving provenance

Repo status:

- future concept; not explicitly implemented today

## How the Engine Maps to Core vs Observability

### Observability owns

- artifact capture
- normalization
- provenance
- classification
- scoring
- candidate records
- telemetry-informed experience extraction
- promotion logs
- deprecation and reinforcement signals

This is the natural home because Observability already contains:

- turns/spans/threads
- working context
- telemetry
- governance
- distillation
- memory-entry eval metadata

### Core owns

- the narrow final destination for promoted durable semantic memory blocks
- stable retrieval and persistence once promotion is already decided

This preserves:

- Core as the stable memory sidecar
- Observability as the experimental continuity/promotion engine

## Example Artifact Flow

Example artifact:

> “Core should remain the stable memory sidecar, Observability owns conversation-centric capabilities.”

Possible routing path:

1. **Raw archive**
   - captured as conversation turns/imported discussion artifacts in Observability
1. **Working memory**
   - appears in the current working context while architectural discussion is active
1. **Episodic memory**
   - stored as a notable architecture decision episode tied to a specific discussion/run
1. **Durable semantic memory**
   - promoted only if repeated and stable enough to become a durable repo fact or project principle
1. **Policy / constraints**
   - if it becomes a project-wide architectural constraint, it may be elevated into policy/constraints documentation rather than ordinary memory
1. **Procedural / experience lesson**
   - if repeated work shows that keeping Core stable and putting conversation features in Observability consistently reduces churn, that becomes an experience/procedural lesson

Why this example matters:

- the same artifact may validly exist in multiple layers for different reasons
- promotion is not a single yes/no decision
- repo-aligned architecture needs both provenance and restraint

## What Is Current vs Future

### Implemented now

- Core durable memory runtime
- Core save heuristics and session logic
- Observability turns/spans/working context
- Observability telemetry/governance
- Observability semantic/procedural distillation
- existing `active` / `deprecated` / `quarantined` style status controls

### Emerging

- procedural memory as a proto-experience layer
- success/failure counters as reinforcement signals
- governance-driven adaptation and context rebuilding

### Future

- explicit Promotion Engine subsystem
- unified promotion scoring model
- explicit candidate/promotion state machine
- durable projection path from Observability memory into Core blocks
- retirement lifecycle
- human-gated promotion workflows

## Recommended Phased Implementation Sequence

1. **Document the Promotion Engine**
   - terminology, states, scoring, ownership boundaries
1. **Define normalized artifact and provenance interfaces**
   - stay in Observability
1. **Add candidate/promotion metadata to Observability models**
   - only after the design stabilizes
1. **Wire reinforcement/deprecation signals**
   - use existing telemetry/governance/eval counters
1. **Introduce explicit projection rules into Core**
   - only for durable semantic memory
1. **Add human-gated paths for policy/high-risk promotion**
   - later phase

This sequence keeps changes incremental and preserves the current Core vs Observability split.
