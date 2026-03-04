from __future__ import annotations


def _create_conversation(client, headers, title="acc", settings=None):
    payload = {"title": title}
    if settings:
        payload["settings"] = settings
    r = client.post("/v2/conversations", json=payload, headers=headers)
    assert r.status_code == 200
    return r.json()


def _add_turn(client, headers, cid, speaker, text, thread_hint=None):
    r = client.post(
        f"/v2/conversations/{cid}/turns",
        json={"speaker": speaker, "text": text, "thread_hint": thread_hint},
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()


def _segment(client, headers, cid):
    r = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=headers)
    assert r.status_code == 200


def test_cross_thread_coupling_detects_off_topic(client, auth_headers):
    c = _create_conversation(client, auth_headers, title="cross-thread")
    cid = c["conversation_id"]

    _add_turn(client, auth_headers, cid, "user", "Diagnose packet loss over wifi networking", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "Check ping, traceroute, and channel congestion.", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "user", "How does dark matter shape galaxies?", thread_hint="cosmology")
    t = _add_turn(client, auth_headers, cid, "assistant", "Dark matter influences gravitational lensing.", thread_hint="cosmology")
    _segment(client, auth_headers, cid)

    wc = client.post(
        f"/v2/conversations/{cid}/working_context",
        json={"query": "networking packet loss troubleshooting", "target_thread_mode": "auto"},
        headers=auth_headers,
    )
    assert wc.status_code == 200
    assert wc.json()["target_thread_id"] == "networking"

    telem = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "networking packet loss troubleshooting", "mode": "minimal"},
        headers=auth_headers,
    )
    assert telem.status_code == 200
    snap = telem.json()["snapshots"][0]
    assert snap["target_thread_id"] == "networking"
    assert snap["metrics"]["off_thread_coupling_Coff"] <= 0.25


def test_governance_rebuilds_on_spike(client, auth_headers):
    c = _create_conversation(
        client,
        auth_headers,
        title="governance",
        settings={"target_thread_mode": "pinned", "pinned_thread_id": "networking", "telemetry_mode": "standard"},
    )
    cid = c["conversation_id"]

    _add_turn(client, auth_headers, cid, "user", "network diagnostics packet loss", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "check baseline metrics", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "user", "cosmology cosmic inflation CMB anisotropy", thread_hint="cosmology")
    t = _add_turn(client, auth_headers, cid, "assistant", "cosmology details", thread_hint="cosmology")
    _segment(client, auth_headers, cid)

    warm = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "network diagnostics", "mode": "minimal"},
        headers=auth_headers,
    )
    assert warm.status_code == 200

    spike = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "cosmology cosmic inflation", "mode": "minimal"},
        headers=auth_headers,
    )
    assert spike.status_code == 200
    snap = spike.json()["snapshots"][0]
    assert snap["metrics"]["alarms"]["off_thread_spike"] is True

    gov = client.post(
        f"/v2/conversations/{cid}/governance/apply",
        json={"snapshot_id": snap["snapshot_id"]},
        headers=auth_headers,
    )
    assert gov.status_code == 200
    data = gov.json()
    assert data["rebuilt_context"] is True
    assert len(data["quarantined_spans"]) >= 1

    span_lookup = {
        s["span_id"]: s
        for s in client.get(
            f"/v2/conversations/{cid}/spans?include_quarantined=true",
            headers=auth_headers,
        ).json()
    }
    selected = data["working_context"]["selected_span_ids"]
    target_count = sum(1 for sid in selected if span_lookup[sid]["thread_id"] == "networking")
    ratio = target_count / max(1, len(selected))
    assert ratio >= 0.7


def test_distillation_creates_procedural_memory(client, auth_headers):
    c = _create_conversation(client, auth_headers, title="distill")
    cid = c["conversation_id"]

    _add_turn(client, auth_headers, cid, "user", "Please draft a deployment checklist for our release")
    _add_turn(client, auth_headers, cid, "assistant", "I will provide a stepwise checklist and risks.")
    _add_turn(client, auth_headers, cid, "user", "Task done, thanks")

    _segment(client, auth_headers, cid)

    r = client.post(
        f"/v2/conversations/{cid}/memory/distill",
        json={"trigger": "user_done"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    created_ids = r.json()["created_memory_ids"]
    assert len(created_ids) >= 1

    memories = client.get(f"/v2/memory?conversation_id={cid}&memory_type=procedural", headers=auth_headers)
    assert memories.status_code == 200
    rows = memories.json()
    assert len(rows) >= 1
    content = rows[0]["content"]
    assert "Applicability:" in content
    assert "Steps:" in content
    assert "Failure modes:" in content
