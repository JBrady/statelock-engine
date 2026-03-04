from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def resolve_database_url(
    db_url_env: str | None,
    sqlite_path_env: str | None,
) -> tuple[str, str | None]:
    if db_url_env:
        if db_url_env.startswith("sqlite:///"):
            raw_path = db_url_env[len("sqlite:///") :]
            if raw_path == ":memory:":
                return db_url_env, None
            resolved = Path(raw_path).expanduser()
            if not resolved.is_absolute():
                resolved = (Path.cwd() / resolved).resolve()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{resolved}", str(resolved)
        return db_url_env, None

    sqlite_path = sqlite_path_env or "./data/statelock_v2.db"
    resolved = Path(sqlite_path).expanduser()
    if not resolved.is_absolute():
        resolved = (Path.cwd() / resolved).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{resolved}", str(resolved)


_db_url, _sqlite_resolved_path = resolve_database_url(
    db_url_env=os.getenv("STATELOCK_DB_URL") or os.getenv("DATABASE_URL"),
    sqlite_path_env=os.getenv("STATELOCK_SQLITE_PATH"),
)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Statelock v2 MVP"
    api_prefix: str = "/v2"
    db_url: str = _db_url
    sqlite_path: str | None = _sqlite_resolved_path
    api_key: str = os.getenv("STATELOCK_API_KEY", "dev-key")


settings = Settings()
