# Session Delta

- Date: `2026-03-06`
- Branch: `main`
- Last Commit: `c4f13c7`
- Focus: post-`v0.4.0` stabilization, idempotent local launcher UX, humane product UI rollout, and rehydration-doc preparation

## Current Focus

- `main` is synced to `origin/main` at merge commit `c4f13c7`.
- The most recent merged work is launcher/lifecycle UX hardening from PR #23.
- The most significant recent product change is the humane product UI from PR #21.
- Local doc work has started for rehydration: `docs/session_context/rehydration-repo-snapshot.md` is currently untracked on `main`.
- This delta file is being added as Layer 3 for the rehydration system.

## Recent Work Completed

- Launcher UX was upgraded from one-shot startup to state-aware startup.
- `make dev-up` is now idempotent and reconciles service state instead of failing on “already running”.
- Stale PID files are now repaired safely in launcher logic.
- Partial-stack recovery is supported.
- `make dev-open` was added.
- `make dev-restart` was added.
- `make dev-status` now renders a human-readable stack summary with overall state, per-service health, and per-service URLs.
- Launcher changes touched `scripts/dev-up.sh`, `scripts/dev-status.sh`, `scripts/lib/dev-common.sh`, `scripts/dev-open.sh`, `scripts/dev-restart.sh`, `Makefile`, and `README.md`.
- Humane product UI MVP landed in `apps/web/`.
- Product-facing routes now exist for Overview, Conversations, Highlights, Memory, Relationships, Runs, and Learning Mode.
- Operator/debug routes were preserved alongside the product UI.
- Release prep for `v0.4.0` landed in `CHANGELOG.md`.
- Architecture/operator docs were aligned and expanded in `docs/`.

## Recent Merged PRs

- PR #23: `dev: make local launcher idempotent` — merged at `2026-03-06T12:46:08Z`
- PR #22: `docs: prepare v0.4.0 release notes` — merged at `2026-03-06T11:52:59Z`
- PR #21: `[codex] Add humane product UI MVP alongside operator routes` — merged at `2026-03-06T11:42:54Z`
- PR #20: `[codex] align architecture and operator docs` — merged at `2026-03-06T10:34:40Z`
- PR #19: `dev: polish local launcher workflow` — merged at `2026-03-06T05:48:45Z`
- PR #18: `web: fix core sessions partial-load error state` — merged at `2026-03-06T05:17:45Z`

## Current Local Stack

- Preferred full-stack startup remains `make dev-up`.
- Current helper commands are `make dev-status`, `make dev-logs`, `make dev-restart`, `make dev-down`, and `make dev-open`.
- Current local ports:
  - Core: `http://127.0.0.1:8000`
  - Observability: `http://127.0.0.1:8001`
  - Next UI: `http://127.0.0.1:3001`
- Launcher runtime artifacts remain under `.run/`.
- `make dev-open` now ensures the stack is up before opening the UI.
- `make dev-status` now reports human-readable service state instead of raw PID-first status lines.

## New System Capabilities

- Idempotent local startup for the full stack.
- Safe stale-PID repair during launcher reconciliation.
- Partial-stack recovery without tearing down healthy services.
- Human-readable stack status with URLs.
- Humane product UI on `/`.
- Preserved operator launchpad on `/operator`.
- Product UI support for continuity overview, conversation inspection, highlights, split memory views, inspector-first relationships, conversation-scoped runs, and read-mostly learning mode.
- Track-aware UI labeling between Core durable memory and Observability learned memory.
- Release marker now present on `main`: `v0.4.0`.

## Open Questions

- Rehydration docs are not committed yet: `docs/session_context/rehydration-repo-snapshot.md` is local and untracked, and this `docs/session_context/session-delta.md` file is being created now.
- Product UI limitations still reflected in shipped notes:
  - no first-class candidate-memory read model yet
  - runs remain conversation-scoped
  - relationship graph visualization is deferred
- Observability remains isolated under `experimental/observability/`; a future promotion path exists in docs, but no promotion into root `app/observability/` has happened.
- Architecture docs are richer than runtime in some areas, so fresh sessions should keep distinguishing implemented behavior from conceptual future work.

## Next Engineering Tasks

- Decide whether to commit the new rehydration docs into `main`.
- Keep the session rehydration stack aligned across architecture template, repo snapshot, and session delta.
- If rehydration docs are committed, add them to the repo’s normal doc/release workflow.
- Continue launcher polish only additively; current local lifecycle behavior is now substantially better than the original hard-fail flow.
- Continue product UI work without collapsing Core and Observability boundaries.
- Keep documenting known limitations as runtime capabilities catch up to the architecture docs.
