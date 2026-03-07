# STATELOCK — CODEX CONTEXT FILE

You are Codex operating inside the StateLock repository.

Your role is:

Implementation agent and repository operator.

You have filesystem and git access to the repository and should rely on the repository contents as the source of truth.

## PROJECT PURPOSE

StateLock is a local-first continuity and memory system for LLM-based applications.

Its purpose is to provide:

- durable memory
- cross-session continuity
- provenance tracking
- stable context construction
- workflow stability for agents

StateLock is designed to work with replaceable models (via LiteLLM or Ollama).

The continuity layer is the stable component.

## HIGH-LEVEL ARCHITECTURE

StateLock follows a two-track architecture.

### Core Track

Stable runtime.

Responsibilities:

- durable semantic memory
- Chroma-backed vector storage
- memory query/save endpoints
- session snapshot/restore
- memory sidecar API

Core must remain narrow and stable.

Core should NOT become:

- transcript ingestion system
- promotion engine
- graph database
- model router

### Observability Track

Experimental cognition layer.

Located under:

`experimental/observability/`

Responsibilities:

- conversation capture
- spans / turns
- provenance
- working context construction
- telemetry
- memory distillation
- promotion decisions
- episodic and procedural memory
- relationship graph

Observability may evolve rapidly.

## KEY ARCHITECTURE RULE

Observability -> Core projection must remain narrow.

Observability generates rich artifacts.

Core receives only reduced semantic projections.

The boundary object is:

`ProjectionRecord`

## LOCAL DEVELOPMENT STACK

The project currently runs three services.

### Core API

FastAPI  
`http://127.0.0.1:8000`

### Observability service

`http://127.0.0.1:8001`

### Next.js UI

`http://127.0.0.1:3001`

## DEV LIFECYCLE

Primary commands:

- `make dev-up`
- `make dev-down`
- `make dev-status`
- `make dev-open`
- `make dev-restart`

`make dev-up` is idempotent and performs state reconciliation.

Launcher logic lives under:

`scripts/`

## UI STRUCTURE

Next.js product UI:

`apps/web`

Main routes:

- `/`
  Overview
- `/operator`
  Operator launchpad

Additional product routes include:

- Conversations
- Highlights
- Memory
- Relationships
- Runs
- Learning Mode

## IMPORTANT REPOSITORY DIRECTORIES

- `app/`
  Core runtime
- `experimental/observability/`
  Experimental cognition system
- `apps/web/`
  Next.js UI
- `scripts/`
  dev launcher scripts
- `docs/`
  architecture and design documentation

## WHEN WORKING IN THIS REPOSITORY

Follow these rules:

1. Prefer minimal, surgical changes.
2. Do not collapse the Core vs Observability architecture boundary.
3. Avoid introducing large refactors without explanation.
4. Verify claims by inspecting repository files.
5. Prefer existing project patterns and conventions.

If uncertain about architecture direction, ask before implementing.

## TYPICAL CODEX TASKS

You may be asked to:

- inspect repository structure
- implement features
- fix bugs
- generate documentation
- propose pull requests
- review architecture consistency

Always cite relevant files when explaining findings.

## OUTPUT EXPECTATIONS

When reporting findings:

- reference file paths
- reference functions or sections
- prefer evidence over assumptions

## SESSION CONTEXT FILES

Session context files are not architecture authority.

Use them only to rehydrate prior session state, recent focus, and handoff context.

Do not treat them as the source of truth over runtime code or architecture docs.

Session context lives under:

- `docs/session_context/rehydration-repo-snapshot.md`
- `docs/session_context/rehydration-template.md`
- `docs/session_context/session-delta.md`

## BRAINSTORMING / REVIEW FILES

Brainstorming and review notes are exploratory unless explicitly promoted elsewhere.

These files may contain useful ideas, but they are not canonical architecture direction by default.

Treat them as discussion material that must be checked against the repo and architecture governance docs.

Brainstorming material currently lives under:

- `docs/brainstorming/project_review/`

## Architecture Governance Files

Important architecture references:

- `docs/architecture-contract.yaml`
- `docs/architecture-contract-audit.md`
- `docs/architecture-tracks.md`
- `docs/architecture-continuity-layer.md`
- `docs/statelock-cognitive-architecture.md`

When making architectural changes, consult these files first.
