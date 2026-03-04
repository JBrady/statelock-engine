# Architecture Tracks

This repository uses a two-track architecture model in a pre-1.0 lifecycle.

- Core Track: canonical runtime for memory sidecar operations.
- Observability Track: subsystem for agent execution state, traceability, and governance.

## Pre-1.0 Versioning Policy

StateLock is pre-1.0 and uses `0.x` semantic versioning milestones (for example `v0.2.0-alpha.1`).

Existing `/v2/*` route namespaces are treated as legacy route labels only. They are not architecture version markers.

## Core Track Responsibilities

Core Track is the canonical runtime and includes:

- `/memories/*` APIs
- memory block storage and retrieval
- insights endpoints
- `/healthz` and `/readyz`
- ChromaDB-backed persistence
- operational stack (Docker, CI, examples)

## Observability Track Responsibilities

Observability Track includes:

- conversations, turns, spans
- working context construction
- execution telemetry and explainability
- governance actions and auditability
- conversation export/import bundles
- traceability of agent runs

## Current Isolation Model

Observability code is imported under:

- `experimental/observability/`

This isolation is intentional to reduce risk while preserving history and allowing staged promotion.

## Long-Term Intended Layout (Post-Promotion)

After promotion from `experimental/observability/`, the target structure is:

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

Promotion is incremental and must preserve subsystem coherence; observability components should not be scattered across unrelated directories.

## Route Compatibility and Future Alias Strategy

- Existing `/v2/*` routes remain supported for compatibility.
- A future additive alias (for example `/obs/*`) may be introduced.
- Any aliasing must be non-breaking and must not remove or regress existing `/v2/*` behavior.
