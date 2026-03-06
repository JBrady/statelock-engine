# StateLock v2 Repository Guide

## 1. Purpose
StateLock v2 is a local-first context-hygiene engine for long-running LLM conversations.

For phase/status context, see `docs/ROADMAP.md`.

It helps an assistant:
- keep evidence organized by topic thread,
- build a bounded working context,
- measure how much each span influences generation,
- detect context rot,
- apply governance actions,
- distill durable memory.

This repo is intentionally minimal and deterministic so behavior is reproducible in local development and tests.

## 2. Core Design Principles
- Deterministic: stable heuristics and a deterministic stub backend make tests reliable.
- Local-first: FastAPI + SQLite, no distributed services, no vector DB.
- Debuggable: pipeline logs, telemetry snapshots, explain endpoints, and dashboard views.
- Backward-compatible iteration: additive APIs and no schema-breaking changes.

## 3. Technology Stack
- API: FastAPI
- Persistence: SQLite via SQLAlchemy ORM
- Validation/serialization: Pydantic
- Testing: pytest
- UI: server-rendered Jinja templates + small vanilla JS

## 4. Repository Layout
- `app/main.py`: FastAPI app bootstrap, router registration, health endpoint.
- `app/config.py`: settings and deterministic DB URL/path resolution.
- `app/runtime.py`: process/runtime metadata (`STARTED_AT`, `CWD`, `GIT_SHA`).
- `app/db/`: SQLAlchemy models, engine/session, DB init.
- `app/api/`: HTTP routes.
- `app/pipelines/`: segmentation and thread inference helpers.
- `app/context_builder/`: working context assembly and budget pruning.
- `app/telemetry/`: influence, ablation, and metrics math.
- `app/services/`: orchestration/query/service helpers.
- `app/memory/`: ReMe-style memory distillation.
- `app/governance/`: governance actions.
- `app/backends/stub_llm.py`: deterministic logits/proxy backend for telemetry.
- `app/templates/`, `app/static/`: minimal dashboard and docs UI.
- `scripts/`: seeding and example API call script.
- `tests/`: unit, integration, and acceptance tests.
- `docs/`: implementation decisions and onboarding docs.

## 5. Data Model (Tables)
Defined in `app/db/models.py`:
- `conversations`: conversation-level settings and metadata.
- `turns`: user/assistant/tool messages.
- `spans`: segmented chunks with trust/provenance/thread assignment.
- `threads`: topical clusters of spans.
- `working_contexts`: assembled context payloads + selection logs.
- `telemetry_snapshots`: influence snapshots (proxy and ablation rows).
- `memory_entries`: distilled semantic/procedural/episodic memory.
- `governance_events`: audit log of governance/manual actions.
- `pipeline_logs`: lightweight pipeline stage logs.

## 6. Main Pipelines

### 6.1 Segmentation + Threading
1. Turns are segmented into spans.
2. Spans are assigned to thread IDs.
3. Thread records are updated (`span_count`, `last_activity_at`).

Routes:
- `POST /v2/conversations/{conversation_id}/segment`
- `GET /v2/conversations/{conversation_id}/threads`

### 6.2 Working Context Builder
Input: query + conversation settings.

High-level behavior:
1. Infer target thread (`auto` or `pinned`).
2. Select up to 2 procedural memories.
3. Score spans using relevance/recency/trust.
4. Build evidence set with limited off-thread allowance.
5. Expand via provenance links.
6. Assemble sections: procedures, key facts, recent turns, evidence, tool outputs.
7. Enforce token budget with explicit pruning order.
8. Guarantee non-empty evidence when candidates existed (`fallback_keep_best_span`).

Pruning order under pressure:
1. trim recent turns,
2. compress long tool outputs,
3. drop low trust,
4. drop old unused,
5. drop low relevance,
6. fallback keep best span if evidence would become empty.

Routes:
- `POST /v2/conversations/{conversation_id}/working_context`
- `GET /v2/conversations/{conversation_id}/working_context/latest`

### 6.3 Telemetry (Proxy + Measured Ablation)
Orchestrated by `app/services/telemetry_service.py`.

Behavior:
1. Build current working context.
2. Always compute proxy influence and persist one `grad_proxy` snapshot.
3. In scheduled modes (`standard` cadence or always for `verbose`), run KL ablation and persist a second `ablation_kl` snapshot with same `run_group_id`.
4. Compute metrics and alarms per snapshot.

Telemetry rows are separate when both methods run.

Routes:
- `POST /v2/conversations/{conversation_id}/telemetry`
- `GET /v2/conversations/{conversation_id}/telemetry/latest`
- `GET /v2/conversations/{conversation_id}/telemetry/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/{run_group_id}`
- `GET /v2/conversations/{conversation_id}/telemetry/snapshots/{snapshot_id}/explain`

### 6.4 Governance
Triggered from latest or selected telemetry snapshot.

Actions include:
- quarantine off-thread spans on spike,
- reduce trust of stale dominant anchors,
- tighten context selection on smear,
- optionally rebuild working context.

Manual control:
- unquarantine a span.

Routes:
- `POST /v2/conversations/{conversation_id}/governance/apply`
- `GET /v2/conversations/{conversation_id}/governance/log`
- `POST /v2/conversations/{conversation_id}/spans/{span_id}/unquarantine`

### 6.5 ReMe-Style Distillation
- Extract recent turns,
- synthesize semantic and procedural memory candidates,
- merge/deprecate based on title/content overlap,
- persist with provenance.

Routes:
- `POST /v2/conversations/{conversation_id}/memory/distill`
- `GET /v2/memory`

## 7. Telemetry Math (Current Behavior)

### Influence normalization
- `normalize_weights` clamps invalid values (`NaN`, `inf`, negative) to 0.
- If total raw score is zero, weights become uniform.
- Weights are renormalized and drift-corrected to sum to ~1 exactly.

### Entropy
- `H = -sum(w * log(w + eps))`
- Fast-path: `H = 0` for empty or single-item weight sets.
- Clamp tiny negative floating-point artifacts to `0.0`.

### Off-thread coupling
- `W_target = sum(weights for spans in target thread)`
- `Coff = 1 - W_target`
- Clamp `Coff` into `[0, 1]` for numeric stability.

### KL ablation definition
- Uses first generated token distribution only:
  - baseline `p = softmax(logits(Z))`
  - ablated `q_i = softmax(logits(Z \ i))`
  - influence `I_i = KL(p || q_i)`
- Normalize ablation influences into final `w` values.

## 8. Deterministic Stub Backend
`app/backends/stub_llm.py` is used so tests are meaningful without external model calls.

- Span IDs map deterministically to vectors.
- Logits are additive from base + selected span vectors.
- Removing a span deterministically changes logits, yielding stable KL deltas.

## 9. API Surface Summary

### JSON API routes (`/v2/*`)
Conversation and turns:
- `POST /v2/conversations`
- `GET /v2/conversations`
- `GET /v2/conversations/{conversation_id}`
- `PATCH /v2/conversations/{conversation_id}`
- `POST /v2/conversations/{conversation_id}/turns`
- `GET /v2/conversations/{conversation_id}/turns`

Segmentation/threads/context:
- `POST /v2/conversations/{conversation_id}/segment`
- `GET /v2/conversations/{conversation_id}/threads`
- `POST /v2/conversations/{conversation_id}/working_context`
- `GET /v2/conversations/{conversation_id}/working_context/latest`

Telemetry:
- `POST /v2/conversations/{conversation_id}/telemetry`
- `GET /v2/conversations/{conversation_id}/telemetry/latest`
- `GET /v2/conversations/{conversation_id}/telemetry/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/{run_group_id}`
- `GET /v2/conversations/{conversation_id}/telemetry/snapshots/{snapshot_id}/explain`

Governance and spans:
- `POST /v2/conversations/{conversation_id}/governance/apply`
- `GET /v2/conversations/{conversation_id}/governance/log`
- `GET /v2/conversations/{conversation_id}/spans`
- `POST /v2/conversations/{conversation_id}/spans/{span_id}/unquarantine`

Memory:
- `GET /v2/memory`
- `POST /v2/conversations/{conversation_id}/memory/distill`

Portability and debugging:
- `GET /v2/conversations/{conversation_id}/export`
- `POST /v2/conversations/import`
- `GET /v2/debug/info`

### HTML routes (not under `/v2`)
- `/`
- `/learn`
- `/threads`
- `/memory`
- `/spans`
- `/telemetry/run_group/{run_group_id}`

## 10. Local Development

If you are onboarding, start with:
- `docs/FIRST_30_MINUTES.md`

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Repo-root launcher note:

- standalone Observability uses `127.0.0.1:8000`
- repo-root `make dev-up` launches Observability on `127.0.0.1:8001`

### DB location
Default SQLite path is `./data/statelock_v2.db`.

Resolved path behavior:
- always resolved to an absolute path,
- parent directory auto-created,
- path shown at startup.

Override:
- `STATELOCK_SQLITE_PATH=...`
- or full `STATELOCK_DB_URL=...`

### Auth
All `/v2/*` routes require:
- `Authorization: Bearer dev-key`

### Make targets
- `make setup`
- `make run`
- `make test`
- `make seed`

## 11. Testing Strategy
- Unit tests: math, candidate set logic, context pruning behavior, DB path config.
- Integration tests: endpoint behavior, telemetry views, export/import, dashboard pages, health/debug info.
- Acceptance tests: cross-thread coupling, governance behavior, distillation outcomes.

Run:
```bash
pytest -q
```

## 12. Operational Tips
- Use `/health` for process/DB identity.
- Use `/v2/debug/info` when diagnosing “wrong DB” incidents.
- Use `/v2/conversations/{id}/telemetry/run_groups/recent` for quick telemetry trend inspection.
- Use `/v2/conversations/{id}/telemetry/snapshots/{snapshot_id}/explain` for per-snapshot diagnostics.
- Use `/v2/conversations/{id}/export` and `/v2/conversations/import` to move conversation state between environments.
