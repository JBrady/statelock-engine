# statelock-v2 MVP

Local-first MVP implementing context hygiene, telemetry, governance, and memory distillation.

## Stack

- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- pytest

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

By default, SQLite data is stored at `./data/statelock_v2.db` (resolved to an absolute path at startup).
Override with:

```bash
export STATELOCK_SQLITE_PATH=./data/my_custom.db
# or
export STATELOCK_DB_URL=sqlite:///./data/my_custom.db
```

Auth header required for `/v2/*` routes:

```text
Authorization: Bearer dev-key
```

## Dashboard

- `/`
- `/threads`
- `/memory`

## Tests

```bash
pytest -q
```

## Notes

- Telemetry stores proxy and ablation as separate snapshots with a shared run group id.
- See `docs/decisions.md` for deterministic token estimation and KL definition.
