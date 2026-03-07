# StateLock Repo Snapshot

Repo snapshot for session rehydration, grounded in the current synced `main` branch on 2026-03-06.

## 1. Directory Structure

Top-level repo shape:

```text
app/                        Core FastAPI runtime
apps/web/                   Next.js App Router UI
docs/                       Architecture, operator, launcher, and workflow docs
examples/                   Integration and smoke-test examples
experimental/observability/ Observability subsystem
infra/cloudflare/           Website/domain ops assets
scripts/                    Local launcher and helper scripts
site/                       Static website/local console assets
tests/                      Core test suite
chroma_db/                  Local Chroma persistence
.run/                       Local launcher PID/log artifacts
```

Important subdirectories:

- `app/core/`: config, auth, database, error handling
- `app/routers/`: Core HTTP routes
- `app/services/`: Core memory, embedding, automation-policy logic
- `apps/web/app/`: product and operator UI routes
- `experimental/observability/app/api/`: Observability HTTP surface
- `experimental/observability/app/db/`: SQLAlchemy models and DB init
- `experimental/observability/app/context_builder/`: active-context assembly
- `experimental/observability/app/memory/`: distillation pipeline
- `experimental/observability/app/governance/`: governance actions
- `experimental/observability/app/telemetry/`: telemetry metrics, influence, ablation

## 2. Core Services

Core entrypoint:

- [`main.py`](../main.py) boots the Core FastAPI app.

Core responsibilities, consistent with [`README.md`](../README.md) and [`docs/architecture-tracks.md`](./architecture-tracks.md):

- durable memory sidecar runtime
- Chroma-backed persistence
- CRUD and query APIs for memory blocks
- hybrid query with recency + similarity
- session snapshot/restore
- stats, sessions, and tags endpoints
- `/healthz` and `/readyz`
- optional API-key auth and structured error envelopes

Primary Core route files:

- [`app/routers/memories.py`](../app/routers/memories.py)
  - `POST /memories/`
  - `POST /memories/upsert`
  - `POST /memories/query`
  - `POST /memories/query-hybrid`
  - `GET /memories`
  - `DELETE /memories/bulk`
  - `DELETE /memories/session/{session_id}`
  - `GET /memories/session/{session_id}/snapshot`
  - `POST /memories/session/{session_id}/restore`
  - `DELETE /memories/{block_id}`
- [`app/routers/insights.py`](../app/routers/insights.py)
  - `GET /stats/overview`
  - `GET /sessions`
  - `GET /tags`

Core service layer:

- [`app/services/memory_service.py`](../app/services/memory_service.py): canonical memory read/write/query implementation
- [`app/services/embedder.py`](../app/services/embedder.py): embedding abstraction
- [`app/services/automation_policy.py`](../app/services/automation_policy.py): explicit save-policy helpers

## 3. Observability Components

Observability entrypoint:

- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py)

Observability is intentionally isolated under `experimental/observability/` and owns richer continuity logic:

- conversations and turns
- spans/highlights
- thread segmentation
- working-context construction
- telemetry capture and explainability
- governance actions and audit logging
- memory distillation
- conversation import/export

Primary Observability route files:

- [`experimental/observability/app/api/conversations.py`](../experimental/observability/app/api/conversations.py)
  - conversation create/list/get/update
  - conversation import/export bundle
- [`experimental/observability/app/api/turns.py`](../experimental/observability/app/api/turns.py)
  - add/list turns for a conversation
- [`experimental/observability/app/api/spans.py`](../experimental/observability/app/api/spans.py)
  - list spans, optional thread filter, optional quarantined inclusion
- [`experimental/observability/app/api/segmentation.py`](../experimental/observability/app/api/segmentation.py)
  - segment conversation into threads
  - list threads
- [`experimental/observability/app/api/context.py`](../experimental/observability/app/api/context.py)
  - build working context
  - fetch latest working context
- [`experimental/observability/app/api/telemetry.py`](../experimental/observability/app/api/telemetry.py)
  - run telemetry
  - list latest/recent snapshots
  - list recent run groups
  - run-group detail
  - snapshot explainability
- [`experimental/observability/app/api/memory.py`](../experimental/observability/app/api/memory.py)
  - list distilled memory entries
  - trigger memory distillation
- [`experimental/observability/app/api/governance.py`](../experimental/observability/app/api/governance.py)
  - apply governance actions
  - governance log
  - unquarantine span
- [`experimental/observability/app/api/dashboard.py`](../experimental/observability/app/api/dashboard.py)
  - server-rendered dashboard surface
- [`experimental/observability/app/api/debug.py`](../experimental/observability/app/api/debug.py)
  - debug API surface

Key supporting components:

- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py): conversations, turns, spans, threads, working contexts, telemetry snapshots, memory entries, governance events, pipeline logs
- [`experimental/observability/app/context_builder/builder.py`](../experimental/observability/app/context_builder/builder.py): active-context assembly
- [`experimental/observability/app/memory/distill.py`](../experimental/observability/app/memory/distill.py): ReMe-style distillation path
- [`experimental/observability/app/services/telemetry_service.py`](../experimental/observability/app/services/telemetry_service.py): telemetry orchestration
- [`experimental/observability/app/services/export_import.py`](../experimental/observability/app/services/export_import.py): bundle import/export
- [`experimental/observability/app/backends/stub_llm.py`](../experimental/observability/app/backends/stub_llm.py): deterministic backend for telemetry/tests

## 4. Launcher System

Current local launcher entrypoint:

- [`Makefile`](../Makefile)

Available commands:

- `make dev-up`
- `make dev-down`
- `make dev-status`
- `make dev-restart`
- `make dev-logs`
- `make dev-open`

Launcher scripts:

- [`scripts/dev-up.sh`](../scripts/dev-up.sh): idempotent full-stack startup
- [`scripts/dev-down.sh`](../scripts/dev-down.sh): stop launcher-managed services
- [`scripts/dev-status.sh`](../scripts/dev-status.sh): human-readable stack status
- [`scripts/dev-restart.sh`](../scripts/dev-restart.sh): stop then start
- [`scripts/dev-open.sh`](../scripts/dev-open.sh): ensure stack is up, then open UI
- [`scripts/dev-logs.sh`](../scripts/dev-logs.sh): tail `.run/logs`
- [`scripts/lib/dev-common.sh`](../scripts/lib/dev-common.sh): shared launcher logic

Current launcher behavior:

- Core runs on `127.0.0.1:8000`
- Observability runs on `127.0.0.1:8001`
- Next UI runs on `127.0.0.1:3001`
- launcher stores PID files and logs under `.run/`
- `make dev-up` is idempotent
- startup reconciles real service state instead of failing on "already running"
- stale PID files are repaired safely
- partial-stack recovery is supported
- status output shows overall state plus per-service health and URLs

The launcher is a dev/operator surface. There is no desktop or app-style end-user launcher in-repo yet.

## 5. UI Routes

Primary UI app:

- [`apps/web/`](../apps/web)

Current UI split:

- humane product shell on `/`
- preserved operator/debug shell on `/operator` and operator-style routes
- legacy local Core static console still mounted by Core at `/app`
- Observability also has a server-rendered dashboard under its own FastAPI app

Humane product routes in `apps/web/app/`:

- `/` -> Overview
- `/conversations`
- `/highlights`
- `/memory`
- `/relationships`
- `/runs`
- `/learning-mode`

Operator/debug routes in `apps/web/app/`:

- `/operator` -> launchpad
- `/metrics`
- `/core/health`
- `/core/query`
- `/core/sessions`
- `/core/stats`
- `/core/tags`
- `/obs/runs`

Important UI shell files:

- [`apps/web/app/layout.tsx`](../apps/web/app/layout.tsx): root shell
- [`apps/web/components/app-shell.tsx`](../apps/web/components/app-shell.tsx): route-aware wrapper
- [`apps/web/components/nav.tsx`](../apps/web/components/nav.tsx): operator navigation
- [`apps/web/components/product/`](../apps/web/components/product): humane product page implementations

Current UI model:

- product UI is additive and lives alongside operator/debug routes
- Core vs Observability boundaries are preserved in the UI
- humane labels are used in the product shell
- technical details are kept in technical drawers/operator surfaces

## 6. Key Architecture Documents

Core/current-boundary docs:

- [`docs/architecture-tracks.md`](./architecture-tracks.md): canonical Core vs Observability track boundary
- [`docs/architecture-continuity-layer.md`](./architecture-continuity-layer.md): continuity-layer rationale and placement
- [`docs/statelock-cognitive-architecture.md`](./statelock-cognitive-architecture.md): broader system model
- [`docs/architecture-sanity-check.md`](./architecture-sanity-check.md): architecture consistency review

Memory/continuity design docs:

- [`docs/architecture-memory-stratification.md`](./architecture-memory-stratification.md)
- [`docs/architecture-memory-graph.md`](./architecture-memory-graph.md)
- [`docs/architecture-memory-policy-profiles.md`](./architecture-memory-policy-profiles.md)
- [`docs/architecture-promotion-engine.md`](./architecture-promotion-engine.md)
- [`docs/architecture-promotion-schemas.md`](./architecture-promotion-schemas.md)

Operator/runtime docs:

- [`docs/local-stack.md`](./local-stack.md)
- [`docs/local-stack-minimal.md`](./local-stack-minimal.md)
- [`docs/local-stack-panic-recovery.md`](./local-stack-panic-recovery.md)
- [`docs/run-with-local-first-stack.md`](./run-with-local-first-stack.md)
- [`docs/operator-runbook.md`](./operator-runbook.md)
- [`docs/dev-workflow.md`](./dev-workflow.md)
- [`docs/release-checklist.md`](./release-checklist.md)

Website/domain ops docs:

- [`docs/domain-operations.md`](./domain-operations.md)
- [`docs/website-routing.md`](./website-routing.md)

## 7. Recently Merged PRs

Recent merges on `main`:

1. PR #23
   - merge commit: `c4f13c7`
   - title: `dev: make local launcher idempotent`
   - outcome: idempotent launcher, better status output, stale-PID repair, partial-stack recovery, `dev-open`, `dev-restart`
1. PR #22
   - merge commit: `60b0f51`
   - title: `docs: prepare v0.4.0 release notes`
   - outcome: release-prep/changelog work for `v0.4.0`
1. PR #21
   - merge commit: `76e5470`
   - title: `web: add humane product UI MVP`
   - outcome: humane product UI added alongside operator routes
1. PR #20
   - merge commit: `c1c466c`
   - title: `docs: align architecture and operator docs`
   - outcome: architecture and launcher/operator docs cleanup
1. PR #19
   - merge commit: `4fa85b1`
   - titles in branch history:
     - `dev: add local stack launcher scripts`
     - `dev: polish local launcher workflow`
   - outcome: repo-root local launcher introduced and refined
1. PR #18
   - merge commit: `fbb58d4`
   - title: `web: fix core sessions partial-load error state`

Release markers:

- current tag on main: `v0.4.0`

## 8. Known Experimental Subsystems

Primary experimental subsystem:

- [`experimental/observability/`](../experimental/observability)
  - richest continuity/telemetry/governance subsystem
  - intentionally isolated from Core pending future promotion

Known example/experimental integration areas:

- [`examples/openclaw-tooling/`](../examples/openclaw-tooling)
  - OpenClaw automation contract and local runtime wiring
- [`examples/agent-memory-loop/`](../examples/agent-memory-loop)
  - agent-memory loop experiments
- [`examples/litellm-client/`](../examples/litellm-client)
  - LiteLLM integration example
- [`examples/real-llm-smoke/`](../examples/real-llm-smoke)
  - smoke path for real model calls
- [`examples/statelock-seed-client/`](../examples/statelock-seed-client)
  - older seed/demo client example

Other noteworthy non-core surfaces:

- [`site/`](../site)
  - static website/local-only worktree surface
- [`site/app/`](../site/app)
  - local Core console assets mounted at `/app` when present

## Snapshot Takeaways

- Core is still the narrow, stable memory sidecar.
- Observability is the richer continuity subsystem and remains isolated under `experimental/observability/`.
- The repo now has both a humane product UI and preserved operator/debug routes.
- The local launcher is now idempotent and state-aware.
- Architecture docs are ahead of some runtime capabilities in places, so repo reality should still win over conceptual design notes during implementation.

## Rehydration Rules

Use this snapshot with the following rules:

- implemented behavior comes from runtime code and current git state first
- architecture docs describe intended direction, but are not proof of implementation by themselves
- if code, docs, and git state disagree, report the mismatch explicitly instead of silently reconciling it
- keep Core narrow; place richer continuity systems in Observability first unless current repo evidence says otherwise

## Role Split Reminder

Current repo-grounded role split:

- LiteLLM handles model alias routing/fallback
- Ollama is the local model runtime
- StateLock handles memory and continuity
- OpenClaw and similar agent integrations should remain adapter-style rather than turning StateLock into a model gateway

StateLock is not a model router. Its stable Core role is durable memory plus narrow retrieval/insight APIs.

## Read First For Fast Rehydration

If starting a fresh session, these files rebuild the highest-signal context quickly:

- [`README.md`](../README.md)
- [`docs/architecture-tracks.md`](./architecture-tracks.md)
- [`docs/local-stack.md`](./local-stack.md)
- [`Makefile`](../Makefile)
- [`main.py`](../main.py)
- [`app/routers/memories.py`](../app/routers/memories.py)
- [`app/services/memory_service.py`](../app/services/memory_service.py)
- [`experimental/observability/app/main.py`](../experimental/observability/app/main.py)
- [`experimental/observability/app/db/models.py`](../experimental/observability/app/db/models.py)
- [`apps/web/lib/proxy.ts`](../apps/web/lib/proxy.ts)

## ARCHITECTURE COMPATIBILITY NOTES

- Core and Observability are compatible as adjacent tracks, not as a single collapsed runtime.
- Core is the implemented durable-memory sidecar and should remain narrow unless the repo shows an explicit promotion path.
- Observability is the implemented home for conversation-centric continuity features: conversations, spans, working context, telemetry, governance, and memory distillation.
- The current humane product UI is compatible with this split: it presents both tracks together, but does not erase their boundary.
- Architecture docs in `docs/` are useful design direction, but some concepts remain only partially represented or conceptual. Fresh sessions should distinguish:
  - implemented now
  - partially represented in code/schema
  - conceptual/future architecture
- Concepts such as promotion artifacts, projection records, memory graph ownership, episodic/procedural layering, and policy profiles should be treated as architecture direction unless directly verified in runtime code.
- StateLock remains compatible with LiteLLM, Ollama, OpenClaw, and similar adapters as a memory/continuity subsystem. It should not be reframed as the model router or gateway unless the repo changes explicitly.
- When docs and runtime disagree, compatibility decisions should follow current code and git state first, then note the architecture intent separately.
