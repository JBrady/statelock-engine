# First 30 Minutes Checklist

Use this checklist to get oriented and verify your local environment quickly.

## 0) Open the right docs first (3 minutes)
Read these in order:
1. `README.md`
2. `docs/REPO_GUIDE.md`
3. `docs/ROADMAP.md`
4. `docs/CHANGE_HISTORY.md`
5. `docs/decisions.md`

## 1) Set up and run locally (5 minutes)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected:
- server starts without import/setup errors
- startup logs include the resolved SQLite path

Default DB:
- `./data/statelock_v2.db`

## 2) Verify service identity and health (2 minutes)
In another terminal:
```bash
curl -s http://127.0.0.1:8000/health | jq .
```

Confirm key fields:
- `ok`
- `resolved_db_url`
- `sqlite_path`
- `pid`
- `started_at`
- `cwd`
- `git_sha`

## 3) Run tests once (5 minutes)
```bash
pytest -q
```

Expected:
- all tests pass

## 4) Run the demo API flow (5 minutes)
```bash
bash scripts/demo_requests.sh --pretty
```

Confirm:
- script prints `CID` and `last TID`
- telemetry endpoints return snapshots
- memory distill endpoint returns created IDs

## 5) Quick product tour in browser (5 minutes)
Open:
1. `http://127.0.0.1:8000/`
2. `http://127.0.0.1:8000/learn`
3. `http://127.0.0.1:8000/spans`

What to check:
- dashboard renders and lists conversations
- learn page explains core concepts
- spans page supports filtering/sorting and unquarantine actions

## 6) Hit core inspection endpoints manually (5 minutes)
Use your `CID` from the demo script:
```bash
TOKEN="dev-key"
BASE="http://127.0.0.1:8000"
CID="<your-conversation-id>"

curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/v2/conversations/$CID/telemetry/recent?limit=10" | jq .

curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/v2/conversations/$CID/telemetry/run_groups/recent?limit=10" | jq .

curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/v2/conversations/$CID/export" | jq .
```

## 7) Understand where to edit (optional follow-up)
- API routes: `app/api/`
- Core logic: `app/context_builder/`, `app/telemetry/`, `app/services/`
- DB schema: `app/db/models.py`
- UI pages: `app/templates/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/acceptance/`

## Common gotchas
- Missing auth header on `/v2/*` routes:
  - use `Authorization: Bearer dev-key`
- DB confusion after path changes:
  - verify `/health` and `/v2/debug/info`
- Editable install fails:
  - rerun `pip install -e ".[dev]"` from repo root
