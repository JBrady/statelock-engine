# StateLock Memory Stratification and Experience Layer

## Executive Summary

The proposed extension is **architecturally sound**, with two important clarifications:

1. The **Experience Layer** fits naturally under `experimental/observability/`, not Core.
1. **Memory stratification** is a strong conceptual model for StateLock, but several layers are still conceptual or only partially represented in the repo today.

The repo already supports the underlying shape:

- Core is a stable memory sidecar with durable memory blocks in Chroma.
- Observability already models conversations, spans, working contexts, telemetry, governance, and distilled memory.
- External adapters such as OpenClaw already operate through tool-style contracts rather than a new `/gateway/*` subsystem.

Evidence:

- [`README.md`](../README.md) lines 3-17 define StateLock as a memory sidecar and state it does not route model calls.
- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 14-34 divide responsibilities between Core and Observability.
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 16-151 show conversations, spans, working contexts, telemetry snapshots, memory entries, governance events, and pipeline logs already modeled.
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md) lines 5-30 and 42-79 show current adapter-style integration.

## Why Experience Is Different From Memory

Plain memory answers “what should be remembered?”

Experience answers “what worked, what failed, and what should influence future behavior?”

That distinction matters because the repo already separates:

- durable facts and retrievable blocks in Core
- evaluation, run outcomes, traceability, and governance in Observability

Repo-grounded evidence for an experience-like substrate already exists:

- telemetry snapshots with metrics/actions in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L95)
- governance events in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L132)
- success/failure counters on memory entries in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L127)
- run-group and snapshot explainability in [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py#L90)
- governance logs and rebuild actions in [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py#L16)

That makes Experience a natural extension of **Observability memory + telemetry + governance**, rather than a new Core concern.

## Proposed Extended Cognitive Loop

Current repo-aligned loop:

```text
Conversation
-> Observation
-> Distillation
-> Memory
-> Context
-> Reasoning
```

Proposed extended loop:

```text
Conversation
-> Observation
-> Distillation
-> Memory
-> Experience
-> Context
-> Reasoning
-> Outcome
-> Experience
```

Repo-aligned interpretation:

- **Conversation**: turns, spans, threads, imported bundles
- **Observation**: evidence extraction and thread assignment
- **Distillation**: semantic/procedural memory proposals
- **Memory**: durable Core blocks plus Observability memory entries
- **Experience**: outcome-conditioned lessons derived from telemetry/governance/evals
- **Context**: working-context builder output
- **Reasoning**: still external to StateLock
- **Outcome**: model/agent result plus measured run effects

Evidence:

- working context in [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L135)
- telemetry in [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py#L63)
- governance in [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L29)
- distillation in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L88)

## The Layered Memory Model

The layered model is useful, but each layer needs to be classified correctly.

### Layer 0: Raw Archive

Definition:

- imported transcripts
- conversation records
- turns/spans
- tool traces
- execution logs

Best owner:

- **Observability**

Repo status:

- **partially represented**

What exists:

- conversations, turns, spans, pipeline logs, telemetry snapshots, governance events already exist in Observability models

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 16-151

What does not exist yet:

- a dedicated raw filesystem archive store such as `archive/platform/conversation_id/raw.json`

Command evidence:

```text
$ rg -n "archive/|raw.json|normalized.json" .
[no relevant matches]
```

### Layer 1: Working Memory

Definition:

- recent conversation state
- active task goals
- temporary constraints

Best owner:

- **Observability / context builder**

Repo status:

- **already exists in substance**

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L81) defines `WorkingContext`
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py#L16) exposes working-context build/latest
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L193) assembles procedures, key facts, recent turns, evidence spans, and tool outputs

Important nuance:

- This is better thought of as **active context state**, not durable memory.

### Layer 2: Durable Semantic Memory

Definition:

- stable user preferences
- project facts
- recurring stable knowledge

Best owner:

- **Core**, with optional upstream generation from Observability distillation

Repo status:

- **already exists in general form**

Evidence:

- Core stores memory blocks in Chroma via [`app/core/database.py`](../app/core/database.py#L10)
- Core CRUD/query APIs via [`app/routers/memories.py`](../app/routers/memories.py#L29)
- Core examples already store preference/fact-shaped memories, e.g. [`examples/agent-memory-loop/README.md`](../examples/agent-memory-loop/README.md#L100)

Nuance:

- Core does not currently type these blocks as “semantic” internally.
- So the layer is conceptually right, but the semantic labeling is mostly external/conceptual today.

### Layer 3: Episodic Memory

Definition:

- notable prior events
- decisions
- solved incidents
- bounded “episodes”

Best owner:

- **Observability first**

Repo status:

- **partially represented**

Evidence:

- `MemoryEntryOut.memory_type` already includes `episodic` in [`experimental/observability/app/schemas/models.py`](../experimental/observability/app/schemas/models.py#L125)
- Observability MVP schema also models `memory_type: enum[episodic, semantic, procedural]` in [`experimental/observability/statelock-v2-mvp.yaml`](../experimental/observability/statelock-v2-mvp.yaml#L144)

Nuance:

- Current distillation implementation in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L106) generates `semantic` and `procedural`, not `episodic`.
- So episodic memory should remain a separate layer conceptually, but it is **not yet fully implemented**.

### Layer 4: Procedural / Experience Memory

Definition:

- strategies that worked
- failure patterns
- workflow preferences
- context heuristics
- tool reliability patterns

Best owner:

- **Observability**

Repo status:

- **emerging / partially represented**

Evidence:

- Observability already stores `procedural` memory entries in [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py#L129)
- The working-context builder explicitly selects procedural memory first in [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L40)
- Memory entries already have evaluation fields `success_count`, `failure_count`, and `last_applied_at` in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py#L127)
- The design spec explicitly includes procedural entries with applicability, steps, and failure modes in [`experimental/observability/statelock-v2-mvp.yaml`](../experimental/observability/statelock-v2-mvp.yaml#L314)

Recommendation:

- Use **procedural / experience memory** as the repo-aligned term.
- “Experience layer” is good as a conceptual umbrella.
- “Experience memory” alone is slightly vague compared with the already-modeled `procedural` category.

### Layer 5: Policy / Identity Layer

Definition:

- explicit user instructions
- trust boundaries
- architecture constraints
- durable policy rules

Best owner:

- **constraints/configuration/policy layer**, not generic memory

Repo status:

- **partially represented, but not as a formal memory layer**

Evidence:

- deterministic save policy rules in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)
- OpenClaw-side save defaults in [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md#L92)
- working-context guardrails are explicitly added in the Observability design spec in [`experimental/observability/statelock-v2-mvp.yaml`](../experimental/observability/statelock-v2-mvp.yaml#L193)

Recommendation:

- Rename this from **“Policy / Identity Memory”** to **“Policy / Constraints Layer.”**
- It behaves more like configuration, rules, and guardrails than like ordinary retrievable memory.

## Most Repo-Aligned Terminology

Recommended naming adjustments:

### Experience Layer

Recommended phrase:

- **Experience / Procedural Layer**

Reason:

- “experience” captures the product vision
- “procedural” matches current repo schema and working-context builder behavior

### Episodic Memory

Recommendation:

- keep **episodic** separate from semantic memory

Reason:

- the schema already distinguishes it conceptually
- episodes and generalized facts serve different retrieval and promotion purposes

### Policy / Identity Layer

Recommendation:

- rename to **Policy / Constraints Layer**

Reason:

- this repo currently treats policy more as rules/guardrails/config than as a normal memory family

## Why StateLock Should Not Let the Current Conversation LLM Be the Sole Memory Authority

The currently bound conversation LLM can help propose interpretations, but it should not be the sole authority for routing or promotion.

Why:

1. The runtime LLM is optimized for answering the current prompt, not for long-horizon storage decisions.
1. The repo already uses deterministic and inspectable logic in key places:
   - save triggers in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L31)
   - working-context assembly in [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L135)
   - telemetry metrics in [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py#L45)
   - governance remediation in [`experimental/observability/app/governance/actions.py`](../experimental/observability/app/governance/actions.py#L47)
1. Provenance and traceability matter. A memory decision should be auditable against turns, spans, telemetry, and policies.

So the correct architectural principle is:

- **LLMs may propose memory candidates**
- **StateLock should decide promotion/routing through a hybrid, provenance-aware pipeline**

## Recommended Hybrid Decision Pipeline

The repo-aligned decision pipeline is:

1. **Deterministic rules**
   - obvious triggers, bans, trust boundaries, explicit commands, policy rules
   - existing precedent: save trigger patterns in [`app/services/automation_policy.py`](../app/services/automation_policy.py#L9)
1. **Cheap classifier / heuristic stage**
   - low-cost scoring for semantic vs episodic vs procedural tendency
   - current precedent: thread inference, span scoring, recency/trust heuristics in [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py#L58)
1. **Stronger distillation pass**
   - higher-cost structured extraction and contradiction/redundancy checks
   - current precedent: distillation critic pass described in [`experimental/observability/statelock-v2-mvp.yaml`](../experimental/observability/statelock-v2-mvp.yaml#L330)
1. **Optional human confirmation for major promotions**
   - use for irreversible or high-impact promotions such as durable architectural policies, user identity changes, or cross-project workflow canon

This preserves safety and auditability without blocking normal operation.

## How Routing and Promotion Decisions Should Work

A repo-aligned rule of thumb:

- keep raw interaction artifacts in Observability
- keep active context in working-context state
- promote stable generalized facts to Core when confidence and usefulness are high
- keep strategy/outcome-conditioned lessons in Observability’s procedural/experience layer until proven durable
- treat policy and trust constraints as explicit rules, not casual LLM-authored memory

### Suggested promotion logic

- **Layer 0 -> Layer 1**: automatic, local to the run
- **Layer 1 -> Layer 3/4**: distillation and telemetry-informed extraction
- **Layer 3/4 -> Layer 2**: only after stronger confidence/provenance thresholds
- **Policy / Constraints**: deterministic or explicit confirmation path

## How This Maps to Core vs Observability

| Layer | Best owner | Repo status |
|---|---|---|
| Raw Archive | Observability | partial / future |
| Working Memory | Observability | current |
| Durable Semantic Memory | Core | current in generic form |
| Episodic Memory | Observability first | partial / future |
| Procedural / Experience Memory | Observability | emerging |
| Policy / Constraints | docs/config/runtime rules | partial / future formalization |

This preserves the Core vs Observability split and stays consistent with:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md)
- [`docs/architecture-continuity-layer.md`](../docs/architecture-continuity-layer.md)
- [`docs/statelock-cognitive-architecture.md`](../docs/statelock-cognitive-architecture.md)

## What Is Current, Emerging, or Future

### Implemented now

- Core memory sidecar runtime
- Core snapshots and insights
- Observability conversations, spans, working context, telemetry, governance
- Observability semantic/procedural distillation
- adapter-style OpenClaw integration

### Emerging

- experience-like evaluation signals on memory entries
- telemetry-driven refinement
- procedural memory as reusable strategy layer

### Future

- explicit raw archive store
- formal episodic-memory promotion path
- explicit projection from Observability memory into Core memory blocks
- richer policy/constraints layer
- human-in-the-loop confirmation for major promotions

## Why This Architecture Is Strong

This framing is strong because it avoids a common failure mode: treating all memory as one undifferentiated bucket.

Instead, it lets StateLock:

- store durable facts in Core
- reason about context and outcomes in Observability
- keep promotion decisions inspectable
- preserve provenance
- learn from outcomes without collapsing into a model-router architecture

That is consistent with the repo’s existing structure and gives a practical path forward.

## Cross-Reference

For the subsystem that decides how artifacts move between these layers, see:

- [`docs/architecture-promotion-engine.md`](../docs/architecture-promotion-engine.md)
- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)
- [`docs/architecture-memory-policy-profiles.md`](./architecture-memory-policy-profiles.md)
