# StateLock v2 Roadmap

This roadmap captures the bigger-picture phases for StateLock v2 and where the repo stands now.

## North Star
StateLock should provide reliable context hygiene for long-running LLM interactions by:
- selecting the right evidence,
- measuring influence deterministically,
- detecting rot early,
- applying safe governance actions,
- preserving useful memory over time.

## Current Status Summary
- Core MVP capabilities are implemented and tested.
- Telemetry inspection and portability endpoints are implemented and tested.
- Dashboard/docs onboarding is implemented.
- Current work focus is hardening, cleanup, and preparation for broader usage.

## Phase Plan

## Phase 1: Core MVP Engine
Status: `Done`

Scope:
- conversations, turns, spans, threads
- working context builder
- telemetry proxy + ablation
- governance actions
- ReMe-style distillation

Exit criteria:
- full end-to-end flow runnable locally
- deterministic behavior
- passing unit/integration/acceptance baseline tests

## Phase 2: Telemetry Inspection + Explainability
Status: `Done`

Scope:
- recent telemetry snapshots endpoint
- run-group aggregation endpoint
- snapshot explain endpoint
- deterministic ordering/tie-break semantics

Exit criteria:
- deterministic ordering under timestamp ties
- run-group summaries with metric preference rules
- explain payload available for debugging

## Phase 3: Dashboard + Docs UX
Status: `Done`

Scope:
- homepage telemetry table + onboarding panel
- run-group detail page
- spans browser with unquarantine control
- `/learn` documentation page

Exit criteria:
- first-time user can inspect telemetry and understand concepts from UI alone

## Phase 4: Portability
Status: `Done`

Scope:
- conversation export endpoint
- conversation import endpoint with deterministic remap
- transaction-safe import with rollback on failure

Exit criteria:
- export/import round-trip preserves entity counts
- failures do not leave partial writes

## Phase 5: Dev Reliability and Local UX
Status: `Done`

Scope:
- stable SQLite path resolution and identity fields
- health/debug metadata for DB/process identity
- improved demo script and Make targets
- packaging fix for editable install

Exit criteria:
- reliable startup after reload/CWD changes
- `pip install -e ".[dev]"` succeeds consistently

## Phase 6: Stabilization and Invariants
Status: `In Progress`

Scope:
- lock critical ordering invariants in tests
- tighten telemetry/latest-vs-recent semantics
- maintain deterministic behavior under edge cases

Known completed items in this phase:
- telemetry math stability hardening
- latest/recent ordering tie-break alignment
- latest == first(recent) invariant test

Remaining items:
- reduce warning noise (timezone-aware UTC migration, template API deprecations)
- add lightweight regression checks around warning-sensitive paths

## Phase 7: Near-Term Enhancements (Optional)
Status: `Planned`

Candidate scope:
- optional conversation stats endpoint (`/v2/conversations/{id}/stats`)
- richer run-group trend summaries on dashboard
- memory quality scoring/inspection helpers

## Phase 8: Production Readiness Track (Future)
Status: `Future`

Possible scope (out of MVP):
- auth hardening beyond dev bearer key
- migration/versioning strategy for long-lived data
- observability packaging and deployment profiles
- performance profiling with larger conversation volumes

## What “Done for v2 MVP” Means
For this repo, v2 MVP is considered done when:
- core architecture works end-to-end locally,
- telemetry/governance/distillation are deterministic and test-covered,
- inspection and portability workflows are available,
- onboarding docs/UI make first-time usage straightforward.

