# statelock-v2 MVP

Local-first context-hygiene and memory engine for long-running LLM conversations.

## Start Here
If you are new to the repo, read these first:
- [Repository Guide](docs/REPO_GUIDE.md)
- [Roadmap](docs/ROADMAP.md)
- [Change History and Rationale](docs/CHANGE_HISTORY.md)
- [Implementation Decisions](docs/decisions.md)
- [First 30 Minutes Checklist](docs/FIRST_30_MINUTES.md)

## What StateLock Does
- Segments conversation turns into evidence spans.
- Clusters spans into topic threads.
- Builds bounded working context for response generation.
- Computes telemetry influence via proxy and measured KL ablation.
- Detects context rot and applies governance actions.
- Distills long conversations into reusable memory entries.

## Stack
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- pytest

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## DB Location
Default database path is `./data/statelock_v2.db`.

Override with:
```bash
export STATELOCK_SQLITE_PATH=./data/my_custom.db
# or
export STATELOCK_DB_URL=sqlite:///./data/my_custom.db
```

## Auth
All `/v2/*` routes require:
```text
Authorization: Bearer dev-key
```

## Dashboard Pages
- `/`
- `/learn`
- `/threads`
- `/memory`
- `/spans`
- `/telemetry/run_group/{run_group_id}?conversation_id={conversation_id}`

## API Highlights
Telemetry inspection:
- `GET /v2/conversations/{conversation_id}/telemetry/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/recent`
- `GET /v2/conversations/{conversation_id}/telemetry/run_groups/{run_group_id}`
- `GET /v2/conversations/{conversation_id}/telemetry/snapshots/{snapshot_id}/explain`

Portability:
- `GET /v2/conversations/{conversation_id}/export`
- `POST /v2/conversations/import`

Ops/debug:
- `GET /health`
- `GET /v2/debug/info`

## Dev Commands
```bash
make setup
make run
make test
make seed
```

## Demo Script
```bash
bash scripts/demo_requests.sh --pretty
# optional:
# --base http://127.0.0.1:8000 --token dev-key
```

The script prints `CID` and `last TID` for reuse.

## Tests
```bash
pytest -q
```
