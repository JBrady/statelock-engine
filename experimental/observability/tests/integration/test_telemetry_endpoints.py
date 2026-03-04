from __future__ import annotations


def _create_conversation(client, headers, title="conv", settings=None):
    body = {"title": title}
    if settings:
        body["settings"] = settings
    r = client.post("/v2/conversations", json=body, headers=headers)
    assert r.status_code == 200
    return r.json()


def _add_turn(client, headers, cid, speaker, text, thread_hint=None):
    payload = {"speaker": speaker, "text": text, "thread_hint": thread_hint}
    r = client.post(f"/v2/conversations/{cid}/turns", json=payload, headers=headers)
    assert r.status_code == 200
    return r.json()


def _segment(client, headers, cid, mode="incremental"):
    r = client.post(f"/v2/conversations/{cid}/segment", json={"mode": mode}, headers=headers)
    assert r.status_code == 200
    return r.json()


def test_telemetry_dual_rows_when_ablation_runs(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "standard"})
    cid = c["conversation_id"]

    last_turn = None
    for i in range(8):
        last_turn = _add_turn(
            client,
            auth_headers,
            cid,
            "user" if i % 2 == 0 else "assistant",
            f"networking issue {i}",
            thread_hint="networking",
        )
    _segment(client, auth_headers, cid)

    r = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": last_turn["turn_id"], "query": "networking issue debug", "mode": "standard"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    snaps = r.json()["snapshots"]
    assert len(snaps) == 2
    assert {s["method"] for s in snaps} == {"grad_proxy", "ablation_kl"}
    assert len({s["run_group_id"] for s in snaps}) == 1


def test_telemetry_proxy_kind_recorded(client, auth_headers):
    c = _create_conversation(client, auth_headers)
    cid = c["conversation_id"]
    t = _add_turn(client, auth_headers, cid, "user", "networking packet loss", thread_hint="networking")
    _segment(client, auth_headers, cid)

    r = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "packet loss", "mode": "minimal"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    snaps = r.json()["snapshots"]
    assert len(snaps) == 1
    assert snaps[0]["method"] == "grad_proxy"
    assert snaps[0]["proxy_kind"] == "lexical"


def test_telemetry_verbose_always_returns_ablation_snapshot(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "verbose"})
    cid = c["conversation_id"]

    t1 = _add_turn(client, auth_headers, cid, "user", "networking baseline diagnostics step 1", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "collect logs and packet traces", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "user", "networking baseline diagnostics step 2", thread_hint="networking")
    _segment(client, auth_headers, cid)

    r = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t1["turn_id"], "query": "networking diagnostics", "mode": "verbose"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    snaps = r.json()["snapshots"]

    assert len(snaps) >= 2
    assert any(s["method"] == "ablation_kl" for s in snaps)
    assert len({s["run_group_id"] for s in snaps}) == 1
