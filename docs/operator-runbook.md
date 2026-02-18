# Operator Runbook

## Local dev run

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
cp .env.example .env
make run
```

## Docker run (dev)

```bash
cp .env.example .env
make up
```

## Docker run (production profile)

```bash
cp .env.example .env
# set AUTH_REQUIRED/STATELOCK_API_KEY in .env as needed
make up-prod
```

## Backup (session snapshot export)

```bash
python scripts/session_snapshot_cli.py export \
  --base-url http://127.0.0.1:8000 \
  --session-id telegram:chat_123:user_9 \
  --out backups/chat_123.snapshot.json
```

## Restore

```bash
python scripts/session_snapshot_cli.py import \
  --base-url http://127.0.0.1:8000 \
  --session-id telegram:chat_123:user_9 \
  --in backups/chat_123.snapshot.json \
  --mode replace
```

## Upgrade

1. Pull latest code.
2. Review `CHANGELOG.md` for interface/env changes.
3. Rebuild/restart:

```bash
make down-prod
make up-prod
```

4. Verify readiness:

```bash
curl -sS http://127.0.0.1:8000/healthz
curl -sS http://127.0.0.1:8000/readyz
```

## Rollback

1. Checkout previous git tag/commit.
2. Restart with previous image/config:

```bash
make down-prod
make up-prod
```

3. Restore required sessions from snapshot files.
