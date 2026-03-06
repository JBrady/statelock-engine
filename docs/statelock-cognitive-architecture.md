# StateLock Cognitive Architecture

## StateLock System Mental Model

StateLock is best understood as a **continuity layer** with two cooperating tracks:

- **Core Track** provides stable durable memory operations.
- **Observability Track** provides conversation structure, working context, telemetry, governance, and distillation.

External systems such as OpenClaw, bots, agent runtimes, and CLI tools sit outside StateLock and call into it through existing APIs and adapter contracts.

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 3-6 define the two-track model.
- [`README.md`](../README.md) lines 3-17 define StateLock as a memory sidecar and say it does not route model calls.
- [`docs/local-stack.md`](../docs/local-stack.md) lines 15-24 and 110-119 place LiteLLM in the router role and StateLock in the continuity/memory role.
- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md) lines 3-11 show current adapter-style tool usage.

## Key Design Idea

The key idea is:

- **Core** remembers durable memory blocks.
- **Observability** understands conversation state and selects what matters now.
- **Adapters** let external systems consume those capabilities without turning StateLock into a model gateway.

This means StateLock’s value is not just storage. It is the combination of:

- durable memory
- context hygiene
- traceability
- distillation
- continuity across agent runs

## What Each Layer Does

### Core Track (Stable Runtime)

Core owns:

- memory block storage
- memory retrieval
- session snapshots and restore
- insights (`/stats/overview`, `/sessions`, `/tags`)
- health/readiness
- Chroma-backed persistence

Evidence:

- [`README.md`](../README.md) lines 19-32
- [`app/core/database.py`](../app/core/database.py) lines 10-20
- [`app/routers/memories.py`](../app/routers/memories.py) lines 29-99
- [`app/routers/insights.py`](../app/routers/insights.py) lines 14-39
- [`app/services/memory_service.py`](../app/services/memory_service.py) lines 98-166, 167-257, and 375-421

### Observability Track (Continuity Engine)

Observability owns:

- conversations
- turns
- spans
- working-context construction
- telemetry
- governance
- import/export bundles
- memory distillation
- run traceability

Evidence:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 25-34
- [`experimental/observability/README.md`](../experimental/observability/README.md) lines 13-20
- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py) lines 42-55
- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py) lines 16-46
- [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py) lines 25-132
- [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py) lines 16-56
- [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py) lines 16-45

### Distilled Memory Layer

The distilled-memory idea is conceptually correct, but the repo nuance matters:

- **today**: distillation creates Observability `MemoryEntry` records
- **future possibility**: some distilled outputs may be projected into Core memory blocks

What is true now:

- Distillation exists in Observability via [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 88-158.
- Distilled records currently live in Observability’s `MemoryEntry` model in [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 112-130.

What is **not** proven now:

- automatic promotion of distilled Observability memory into Core Chroma blocks

So the statement “distilled memory becomes Core memory blocks” is best treated as:

- **directionally valid future architecture**
- **not current implementation reality**

### Adapter Layer (Integration Surface)

The adapter layer consists of:

- OpenClaw tools/hooks
- agent runtimes
- CLI workflows
- example adapters

These should interact with:

- Core memory APIs for save/query/session behavior
- Observability context/telemetry APIs when richer continuity is needed

They should **not** force StateLock to become a model router.

Evidence:

- [`docs/run-with-local-first-stack.md`](../docs/run-with-local-first-stack.md) lines 36-43
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md) lines 5-30 and 42-79
- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md) line 98:
  > Cloud escalation remains in agent/router layer; `confidence_low` is only a hint signal.

## The Three Interfaces That Matter

### 1. Normalized conversation bundle schema

Purpose:

- normalize imported chat/export formats before ingestion

Best owner:

- Observability

Why:

- import/export bundles already exist there

Evidence:

- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py) lines 40-62
- [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py) lines 71-121 and 124-260

### 2. Provenance link model

Purpose:

- connect imported conversations, distilled observations, and any later Core memory projection

Best owner:

- Observability first

Why:

- provenance already exists around spans and distilled memory sources

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 46-64
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 112-130
- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 121-123

### 3. External adapter contract for agents and gateways

Purpose:

- expose StateLock memory/context capabilities to OpenClaw-style systems without turning StateLock into a model gateway

Best owner:

- examples/contracts first, runtime promotion later if needed

Evidence:

- [`examples/openclaw-tooling/AUTOMATION_CONTRACT.md`](../examples/openclaw-tooling/AUTOMATION_CONTRACT.md)
- [`examples/openclaw-tooling/README.md`](../examples/openclaw-tooling/README.md)

## Post-1.0 Possibilities

Post-1.0, the repo may promote Observability into a cohesive `app/observability/` subsystem.

That is already anticipated in:

- [`docs/architecture-tracks.md`](../docs/architecture-tracks.md) lines 44-62

The important constraint is that promotion should preserve subsystem coherence:

- Core remains the stable memory runtime
- Observability remains the conversation/traceability/continuity subsystem
- adapters remain at the integration edge

## The Real Product Vision

The real product vision is not “vector DB plus memory CRUD.”

It is:

- durable memory
- context selection
- continuity across runs
- replay and traceability
- outcome-informed refinement

That is why the two-track model is strong:

- Core stays boring and dependable
- Observability carries the more experimental continuity intelligence

## The Clean Mental Model

The cleanest repo-aligned mental model is:

```text
External agents / tools / adapters
            |
            v
        StateLock

  Core Track                Observability Track
  ----------                -------------------
  memory blocks             conversations
  retrieval                 turns / spans / threads
  snapshots                 working context
  insights                  telemetry
  Chroma persistence        governance
                            distillation
                            import/export
                            provenance / replay
```

That is accurate to the current repo.

The only correction to the proposed mental model is:

- “Distilled memory becomes Core memory blocks” should be rewritten as:
  - **distilled memory currently lives in Observability**
  - **it may later be projected into Core memory blocks**

## StateLock Cognitive Loop

The proposed cognitive loop is a good conceptual model:

```text
Conversation
-> Observation
-> Distillation
-> Memory
-> Experience
-> Context
-> Reasoning
-> Outcome
```

But it needs repo-grounded interpretation.

## What Each Stage Does

### Conversation

Conversation is the raw sequence of turns and related metadata.

Repo evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 16-44 define `Conversation` and `Turn`.

### Observation

Observation corresponds to extracting structured evidence spans and thread assignments from conversation turns.

Repo evidence:

- [`experimental/observability/README.md`](../experimental/observability/README.md) lines 13-20
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 46-79 define `Span` and `Thread`

### Distillation

Distillation turns recent conversation evidence into reusable memory entries.

Repo evidence:

- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py) lines 88-158

### Memory

There are two memory notions in the repo:

1. **Core memory blocks** in Chroma
2. **Observability memory entries** derived from conversations

That duality is why the continuity-layer framing matters.

Evidence:

- [`app/core/database.py`](../app/core/database.py) lines 10-20
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 112-130

### Experience

Experience is not a first-class subsystem yet, but it is a plausible next concept.

The repo already has building blocks for it:

- telemetry snapshots with metrics and actions
- governance events
- memory entries with `success_count`, `failure_count`, and `last_applied_at`
- pipeline logs

Evidence:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 95-110 define `TelemetrySnapshot`
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 127-129 define `success_count`, `failure_count`, `last_applied_at`
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py) lines 132-151 define `GovernanceEvent` and `PipelineLog`
- [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py) lines 90-132 expose run-group and snapshot explainability
- [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py) lines 16-56 expose governance actions and logs

This makes the “Experience layer” **viable**, and it fits naturally under:

- `experimental/observability/`

### Context

Context is the bounded, model-visible working set built from procedures, spans, recent turns, and evidence selection logic.

Repo evidence:

- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py) lines 135-200

### Reasoning

Reasoning remains external to StateLock’s current backend runtime.

It happens in:

- LiteLLM / model runtime
- external agents like OpenClaw

Repo evidence:

- [`README.md`](../README.md) lines 11-17
- [`docs/local-stack.md`](../docs/local-stack.md) lines 15-24

### Outcome

Outcome is what the agent/model produced, plus what telemetry/governance later records about whether the context and strategy were good.

Repo evidence:

- telemetry run groups and explainability in [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py)
- governance log in [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py)

## Why This Loop Matters

This loop matters because it explains how StateLock can evolve beyond “just memory retrieval” without forcing all responsibilities into Core.

It gives the repo a coherent future story:

- Core stores durable memory
- Observability turns runs into structured continuity signals
- adapters consume those signals

That preserves the current architecture while still supporting the long-term continuity-layer vision.

## Where Each Part Lives in the Repo

| Concept | Current repo home |
|---|---|
| memory blocks | `app/core/`, `app/services/memory_service.py`, `app/routers/memories.py` |
| insights | `app/routers/insights.py` |
| health/readiness | `main.py` |
| conversations / turns / spans | `experimental/observability/app/db/`, `experimental/observability/app/api/` |
| working context | `experimental/observability/app/context_builder/`, `experimental/observability/app/api/context.py` |
| telemetry | `experimental/observability/app/api/telemetry.py`, `experimental/observability/app/telemetry/` |
| governance | `experimental/observability/app/api/governance.py`, `experimental/observability/app/governance/` |
| distillation | `experimental/observability/app/memory/` |
| adapter examples | `examples/openclaw-tooling/` |

## Architectural Insight

The architecture is sound if read this way:

- Core is the stable substrate.
- Observability is the continuity engine.
- Adapters are the integration surface.

That keeps the repo modular and lets more experimental reasoning-support features mature without destabilizing the canonical memory runtime.

## Why This Architecture Is Strong

This architecture is strong because it avoids two common failures:

1. putting too much experimental reasoning logic into the stable runtime
2. treating memory as only vector retrieval instead of continuity management

The repo already has the beginnings of a stronger pattern:

- a dependable Core
- an experimental but substantial Observability subsystem
- explicit adapter boundaries

## The StateLock Superpower

StateLock’s superpower is not only remembering.

It is:

- deciding what matters from prior interaction
- making that context inspectable
- preserving provenance
- enabling better future reuse

That is why the continuity-layer framing is useful, as long as it stays grounded in the current track boundaries.

## Long-Term Possibility

A plausible long-term direction is:

- imported conversations feed Observability
- Observability extracts distilled and experience-informed knowledge
- selected stable outputs are projected into Core memory blocks
- adapters consume both durable memory and contextual continuity surfaces

That is a realistic evolution from the current repo, and it does not require StateLock to become a model router.

## The One Diagram Explaining the Project

```text
Ollama = model runtime
LiteLLM = model router
OpenClaw / agents / tools = integration edge

                external adapters
                       |
                       v
                  StateLock
         ---------------------------
         |                         |
         v                         v
      Core Track            Observability Track
   memory sidecar           continuity engine
   - memory blocks          - conversations
   - retrieval              - spans / threads
   - snapshots              - working context
   - insights               - telemetry
   - Chroma                 - governance
                             - distillation
                             - import/export
                             - provenance

Reasoning/model invocation stays outside StateLock.
Continuity emerges from Core durability + Observability context intelligence.
```

