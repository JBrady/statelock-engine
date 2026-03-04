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


def test_telemetry_snapshot_explain_contains_required_keys(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "verbose"})
    cid = c["conversation_id"]

    t = _add_turn(client, auth_headers, cid, "user", "networking packet loss", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "collect ping and traceroute", thread_hint="networking")
    seg = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=auth_headers)
    assert seg.status_code == 200

    telem = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "networking packet loss", "mode": "verbose"},
        headers=auth_headers,
    )
    assert telem.status_code == 200
    snapshot_id = telem.json()["snapshots"][0]["snapshot_id"]

    explain = client.get(
        f"/v2/conversations/{cid}/telemetry/snapshots/{snapshot_id}/explain",
        headers=auth_headers,
    )
    assert explain.status_code == 200

    body = explain.json()
    required = {"snapshot", "influence_weights", "alarm_explanations", "diagnostic_summary"}
    assert required.issubset(body.keys())
    assert isinstance(body["snapshot"], dict)
    assert isinstance(body["influence_weights"], list)
    assert isinstance(body["alarm_explanations"], dict)
    assert isinstance(body["diagnostic_summary"], str)
