# StateLock v2 Change History and Rationale

This document summarizes the major changes made during the MVP implementation and hardening cycle, and why each change was introduced.

## 1. MVP Foundation

### What changed
- Built the initial FastAPI + SQLite + SQLAlchemy + Pydantic service.
- Implemented core entities: conversations, turns, spans, threads, working contexts, telemetry snapshots, memory entries.
- Added segmentation, threading, working-context assembly, telemetry, governance, and distillation pipelines.

### Why
- Provide a runnable local baseline with deterministic behavior.
- Keep architecture aligned with the StateLock spec while staying minimal.

## 2. Deterministic Token Estimation

### What changed
- Standardized `token_count_est` using one deterministic regex-based estimator.
- Applied estimator consistently across segmentation, budget enforcement, and tests.

### Why
- Remove dependency on model-specific tokenizers in an MVP.
- Keep tests stable and budget behavior reproducible.

## 3. Telemetry Structure and Explainability

### What changed
- Telemetry writes separate snapshot rows for proxy and ablation methods.
- Added `run_group_id` linkage between rows from the same telemetry run.
- Added telemetry inspection endpoints:
  - `/telemetry/recent`
  - `/telemetry/run_groups/recent`
  - `/telemetry/run_groups/{run_group_id}`
  - `/telemetry/snapshots/{snapshot_id}/explain`
- Added UI labeling distinction:
  - `Proxy (<proxy_kind>)`
  - `Measured (ablation_kl)`

### Why
- Make telemetry inspection and debugging straightforward.
- Preserve method-level traceability without schema-breaking changes.

## 4. KL Ablation Clarification and Candidate Recipe

### What changed
- Explicitly implemented first-token softmax KL ablation definition.
- Implemented deterministic ablation candidate recipe:
  - top relevance set,
  - top proxy set,
  - must-include newest user span,
  - must-include most recent tool span,
  - dedupe and cap by mode.

### Why
- Ensure consistent measured influence behavior.
- Align tests and implementation with unambiguous selection logic.

## 5. Telemetry Math Stability Hardening

### What changed
- Added robust `normalize_weights` helper for probability-safe normalization.
- Clamped invalid raw values (`NaN`, `inf`, negatives).
- Added fallback to uniform distribution when totals are degenerate.
- Added drift correction to keep sums at 1.
- Hardened entropy and off-thread coupling calculations.

### Why
- Prevent NaNs and tiny floating-point artifacts from polluting alarms/UI.
- Guarantee stable telemetry metrics under edge cases.

## 6. Working Context Reliability Improvements

### What changed
- Enforced evidence fallback guarantee: never return empty evidence if candidates existed.
- Added explicit fallback reason in selection logs.
- Adjusted budget pruning order to trim context sections before dropping evidence.
- Relaxed relevance behavior for pinned-thread mode and protected minimum target evidence.
- Added/updated tests for pruning order and fallback guarantees.

### Why
- Prevent poor UX where valid contexts collapse to no evidence.
- Keep pinned-thread use cases resilient under low lexical overlap.

## 7. Governance Controls

### What changed
- Added manual unquarantine endpoint and dashboard control flow.
- Logged manual governance events.

### Why
- Support operator recovery from over-aggressive quarantine decisions.
- Improve debuggability and governance auditability.

## 8. Stable DB Identity Across Reloads

### What changed
- Added deterministic DB path resolution with default `./data/statelock_v2.db`.
- Ensure `./data` is created automatically.
- Store resolved absolute DB path in settings.
- Added debug and health identity fields (`resolved_db_url`, `sqlite_path`, `pid`, `started_at`, `cwd`, `git_sha`).

### Why
- Fix “conversation disappeared” confusion when reload/cwd changes pointed to different SQLite files.
- Make DB identity explicit during troubleshooting.

## 9. Dashboard and Documentation UI Improvements

### What changed
- Added pages:
  - `/learn`
  - `/spans`
  - `/telemetry/run_group/{run_group_id}`
- Enhanced home dashboard with:
  - onboarding panel,
  - first-run welcome state,
  - run-group telemetry table,
  - influence view and tooltips.

### Why
- Improve usability for first-time and non-expert users.
- Provide visual inspection paths for telemetry and span governance.

## 10. Portability (Export/Import)

### What changed
- Added conversation export endpoint returning scoped bundle.
- Added import endpoint with deterministic ID remapping.
- Import runs in a single transaction with rollback on failure.
- Added version validation (`bundle_version`).
- Preserves timestamps when present; otherwise defaults to now.

### Why
- Enable moving conversation state between machines/environments.
- Avoid partial imports and ambiguous failure states.

## 11. Developer UX and Scripts

### What changed
- Added/kept small Makefile targets (`setup`, `run`, `test`, `seed`).
- Improved `scripts/demo_requests.sh` with:
  - `--pretty`, `--base`, `--token` flags,
  - clear section separators,
  - printed `CID` and last `TID`.
- Added syntax test for demo script (`bash -n`).

### Why
- Reduce friction for local manual verification and demos.
- Keep script checks lightweight and non-brittle.

## 12. Packaging/Startup Repair

### What changed
- Fixed editable install failure by constraining setuptools package discovery to `app*` in `pyproject.toml`.
- Excluded non-package directories like `data*`, `tests*`, `docs*`, `scripts*` from package auto-discovery.

### Why
- Resolve `pip install -e ".[dev]"` failure (`Multiple top-level packages discovered in a flat-layout: ['app', 'data']`).
- Restore consistent local development startup.

## 13. Validation Status
- The repo currently passes `pytest -q`.
- Endpoint registration checks confirm telemetry and export/import routes are available under `/v2/*`.

