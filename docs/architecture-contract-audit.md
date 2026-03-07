# Architecture Contract Audit

## Scope

This audit checks the current repository against [`architecture-contract.yaml`](./architecture-contract.yaml).

It is intentionally lightweight:

- code and current repo layout are treated as implementation truth
- architecture docs are treated as direction unless verified in runtime code

## Overall Assessment

The repo appears **mostly consistent** with the contract.

The current implementation still matches the intended two-track split:

- Core remains narrow and memory-oriented under [`app/`](../app/)
- Observability remains the richer continuity subsystem under [`experimental/observability/`](../experimental/observability/)
- the web UI preserves the track boundary instead of collapsing the two systems into one backend

## Evidence For Consistency

### Core remains narrow

Core routing and schemas are still centered on memory blocks and insights:

- [`app/routers/memories.py`](../app/routers/memories.py)
- [`app/routers/insights.py`](../app/routers/insights.py)
- [`app/models/schemas.py`](../app/models/schemas.py)
- [`app/services/memory_service.py`](../app/services/memory_service.py)

What is present:

- memory CRUD and upsert
- semantic and hybrid query
- session snapshot and restore
- stats, sessions, and tags
- health and readiness

What is notably absent from Core:

- transcript ingestion models
- conversation or turn models
- promotion pipeline objects
- graph ownership
- model-routing logic

That matches the contract.

### Observability owns rich continuity behavior

Observability is still the subsystem that carries conversation-level mechanics:

- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py)
- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py)
- [`experimental/observability/app/api/turns.py`](../experimental/observability/app/api/turns.py)
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py)
- [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py)
- [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py)
- [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py)
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py)
- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py)

This matches the contract’s expectation that Observability owns:

- conversations and turns
- highlights/spans
- working context
- telemetry and explainability
- governance
- learned memory and distillation
- provenance and contradiction signals

### The UI preserves the backend split

The Next app remains a thin front-end layer over separate Core and Observability upstreams:

- [`apps/web/lib/proxy.ts`](../apps/web/lib/proxy.ts)
- [`apps/web/app/layout.tsx`](../apps/web/app/layout.tsx)

The proxy still distinguishes:

- `STATELOCK_CORE_BASE_URL`
- `STATELOCK_OBS_BASE_URL`

That is consistent with the contract rule that the UI should preserve track visibility rather than hide architectural boundaries.

### Launcher and local stack align with current contract

The local stack contract is consistent with the current launcher implementation:

- [`Makefile`](../Makefile)
- [`scripts/dev-up.sh`](../scripts/dev-up.sh)
- [`scripts/dev-down.sh`](../scripts/dev-down.sh)
- [`scripts/dev-status.sh`](../scripts/dev-status.sh)
- [`scripts/dev-restart.sh`](../scripts/dev-restart.sh)
- [`scripts/dev-open.sh`](../scripts/dev-open.sh)
- [`scripts/lib/dev-common.sh`](../scripts/lib/dev-common.sh)
- [`README.md`](../README.md)

Current defaults match the contract:

- Core on `127.0.0.1:8000`
- Observability on `127.0.0.1:8001`
- UI on `127.0.0.1:3001`

## Likely Violations, Ambiguities, Or Drift Risks

### No runtime `ProjectionRecord` exists yet

This is the main gap.

`ProjectionRecord` is described in architecture docs as the intended cross-track boundary object:

- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)
- [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)

But it does **not** currently exist in runtime code under [`app/`](../app/) or [`experimental/observability/`](../experimental/observability/).

Practical implication:

- the architecture direction is clear
- the boundary object is still a design contract, not an implemented schema

This is not a violation of the contract as written, because the contract marks it as intended and not yet implemented. It is still the biggest drift risk if future work starts projecting richer objects into Core without first formalizing the boundary.

### Promotion, graph, and policy-profile docs are ahead of implementation

Several architecture docs describe strong future directions:

- [`docs/architecture-promotion-engine.md`](./architecture-promotion-engine.md)
- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)
- [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)
- [`docs/architecture-memory-policy-profiles.md`](./architecture-memory-policy-profiles.md)

The runtime code currently supports adjacent building blocks, especially in Observability, but not the full schema or lifecycle described in those docs.

Risk:

- future contributors may treat those docs as already implemented unless the repo keeps marking these concepts as future-oriented

### Observability remains both important and still explicitly experimental

The product UI depends on Observability routes and data, but the subsystem still lives under:

- [`experimental/observability/`](../experimental/observability/)

This is repo-consistent, but it is still an ambiguity worth noting:

- operationally important
- architecturally isolated
- not yet promoted into the main app namespace

That is acceptable now, but it is an architecture-sensitive area.

### Local stack port language can still be read two ways

The repo-root launcher uses Observability on `8001`, but standalone Observability docs still discuss `8000` for isolated startup:

- [`README.md`](../README.md)
- [`experimental/observability/README.md`](../experimental/observability/README.md)
- [`experimental/observability/docs/FIRST_30_MINUTES.md`](../experimental/observability/docs/FIRST_30_MINUTES.md)
- [`experimental/observability/docs/REPO_GUIDE.md`](../experimental/observability/docs/REPO_GUIDE.md)

This is not a contract violation, but it is a documentation drift risk if the context is not stated clearly.

## Most Architecture-Sensitive Files And Directories

Highest sensitivity:

- [`app/`](../app/)
- [`main.py`](../main.py)
- [`experimental/observability/`](../experimental/observability/)
- [`apps/web/lib/proxy.ts`](../apps/web/lib/proxy.ts)
- [`apps/web/lib/product/`](../apps/web/lib/product/)
- [`scripts/lib/dev-common.sh`](../scripts/lib/dev-common.sh)
- [`docs/architecture-tracks.md`](./architecture-tracks.md)
- [`docs/architecture-continuity-layer.md`](./architecture-continuity-layer.md)
- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)

Why these matter:

- `app/` is where Core could accidentally absorb forbidden concerns
- `experimental/observability/` is where rich continuity logic should continue to land first
- `apps/web/lib/proxy.ts` is the concrete track boundary in the product UI
- `apps/web/lib/product/` is where the UI can accidentally overstate backend capabilities
- `scripts/lib/dev-common.sh` shapes the real local lifecycle contract developers experience
- the architecture docs above are the primary written boundary definitions contributors will read

## Bottom Line

The repo currently appears **compatible with the contract**.

The main caution is not a current violation inside Core. It is future drift:

- if promotion logic moves into Core
- if graph ownership moves into Core
- if UI copy starts implying implemented projection/graph/profile systems that do not exist
- if `ProjectionRecord` is skipped and rich Observability state starts leaking directly into Core
