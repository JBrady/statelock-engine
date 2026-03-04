from __future__ import annotations


def _create_conversation(client, headers, title="export-source"):
    r = client.post("/v2/conversations", json={"title": title, "settings": {"telemetry_mode": "verbose"}}, headers=headers)
    assert r.status_code == 200
    return r.json()["conversation_id"]


def _add_turn(client, headers, cid, speaker, text, thread_hint=None, tool_name=None):
    payload = {"speaker": speaker, "text": text, "thread_hint": thread_hint}
    if tool_name:
        payload["tool_name"] = tool_name
    r = client.post(f"/v2/conversations/{cid}/turns", json=payload, headers=headers)
    assert r.status_code == 200
    return r.json()


def _prepare_bundle(client, headers):
    cid = _create_conversation(client, headers)
    t1 = _add_turn(client, headers, cid, "user", "Investigate packet loss in branch office", thread_hint="networking")
    _add_turn(client, headers, cid, "assistant", "Gather interface errors and latency metrics", thread_hint="networking")
    _add_turn(client, headers, cid, "tool", "ifconfig + ping outputs", thread_hint="networking", tool_name="diag")

    seg = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=headers)
    assert seg.status_code == 200

    telemetry = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t1["turn_id"], "query": "packet loss remediation", "mode": "verbose"},
        headers=headers,
    )
    assert telemetry.status_code == 200

    distill = client.post(
        f"/v2/conversations/{cid}/memory/distill",
        json={"trigger": "user_done"},
        headers=headers,
    )
    assert distill.status_code == 200

    exported = client.get(f"/v2/conversations/{cid}/export", headers=headers)
    assert exported.status_code == 200
    return cid, exported.json()


def _entity_counts(client, headers, cid):
    turns = client.get(f"/v2/conversations/{cid}/turns", headers=headers)
    spans = client.get(f"/v2/conversations/{cid}/spans?include_quarantined=true", headers=headers)
    threads = client.get(f"/v2/conversations/{cid}/threads", headers=headers)
    snapshots = client.get(f"/v2/conversations/{cid}/telemetry/recent?limit=200", headers=headers)
    memory = client.get(f"/v2/memory?conversation_id={cid}", headers=headers)

    assert turns.status_code == 200
    assert spans.status_code == 200
    assert threads.status_code == 200
    assert snapshots.status_code == 200
    assert memory.status_code == 200

    return {
        "turns": len(turns.json()),
        "spans": len(spans.json()),
        "threads": len(threads.json()),
        "snapshots": len(snapshots.json()["snapshots"]),
        "memory": len(memory.json()),
    }


def test_export_import_preserves_entity_counts(client, auth_headers):
    src_cid, bundle = _prepare_bundle(client, auth_headers)

    imported = client.post("/v2/conversations/import", json=bundle, headers=auth_headers)
    assert imported.status_code == 200
    new_cid = imported.json()["new_conversation_id"]
    assert new_cid != src_cid

    before = _entity_counts(client, auth_headers, src_cid)
    after = _entity_counts(client, auth_headers, new_cid)
    assert after == before


def test_import_returns_id_mapping(client, auth_headers):
    src_cid, bundle = _prepare_bundle(client, auth_headers)

    imported = client.post("/v2/conversations/import", json=bundle, headers=auth_headers)
    assert imported.status_code == 200
    body = imported.json()

    mapping = body["import_map"]
    assert mapping["conversations"][src_cid] == body["new_conversation_id"]
    assert len(mapping["turns"]) == len(bundle.get("turns", []))
    assert len(mapping["spans"]) == len(bundle.get("spans", []))
    assert len(mapping["threads"]) == len(bundle.get("threads", []))
    assert len(mapping["snapshots"]) == len(bundle.get("telemetry_snapshots", []))
    assert len(mapping["memory"]) == len(bundle.get("memory_records", []))


def test_import_invalid_bundle_version_returns_400_and_no_partial_write(client, auth_headers):
    _, bundle = _prepare_bundle(client, auth_headers)

    bundle["bundle_version"] = "unknown-version"
    bad = client.post("/v2/conversations/import", json=bundle, headers=auth_headers)
    assert bad.status_code == 400

    conversations = client.get("/v2/conversations", headers=auth_headers)
    assert conversations.status_code == 200
    assert len(conversations.json()) == 1
