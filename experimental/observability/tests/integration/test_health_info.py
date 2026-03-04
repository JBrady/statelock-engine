from __future__ import annotations

from datetime import datetime


def test_health_includes_db_identity_fields(client):
    r = client.get("/health")
    assert r.status_code == 200

    body = r.json()
    required = {
        "ok",
        "resolved_db_url",
        "sqlite_path",
        "pid",
        "started_at",
        "cwd",
        "git_sha",
    }
    assert required.issubset(set(body.keys()))
    assert body["ok"] is True
    assert isinstance(body["resolved_db_url"], str)
    assert isinstance(body["pid"], int)
    assert isinstance(body["cwd"], str)
    assert isinstance(body["started_at"], str)
    datetime.fromisoformat(body["started_at"])

    assert body["git_sha"] is None or isinstance(body["git_sha"], str)
