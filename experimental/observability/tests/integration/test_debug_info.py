from __future__ import annotations

from datetime import datetime


def test_debug_info_keys_exist(client, auth_headers):
    r = client.get("/v2/debug/info", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    required = {"resolved_db_url", "sqlite_path", "cwd", "pid", "started_at"}
    assert required.issubset(set(body.keys()))

    assert isinstance(body["resolved_db_url"], str)
    assert isinstance(body["cwd"], str)
    assert isinstance(body["pid"], int)
    assert isinstance(body["started_at"], str)
    datetime.fromisoformat(body["started_at"])
