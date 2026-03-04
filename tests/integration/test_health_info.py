from __future__ import annotations


def test_health_includes_db_identity_fields(client):
    r = client.get("/health")
    assert r.status_code == 200

    body = r.json()
    required = {"ok", "resolved_db_url", "sqlite_path", "pid"}
    assert required.issubset(set(body.keys()))
    assert body["ok"] is True
    assert isinstance(body["resolved_db_url"], str)
    assert isinstance(body["pid"], int)
