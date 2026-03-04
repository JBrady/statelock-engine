from __future__ import annotations

from datetime import datetime

from app.db.models import TelemetrySnapshot
from app.db.session import SessionLocal


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


def test_telemetry_recent_orders_limits_and_contains_both_methods(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "verbose"})
    cid = c["conversation_id"]

    t = _add_turn(client, auth_headers, cid, "user", "networking debug one", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "trace route", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "user", "networking debug two", thread_hint="networking")
    _segment(client, auth_headers, cid)

    # two runs -> expected proxy+ablation snapshots in both groups
    for q in ["networking debug one", "networking debug two"]:
        r = client.post(
            f"/v2/conversations/{cid}/telemetry",
            json={"turn_id": t["turn_id"], "query": q, "mode": "verbose"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    # force tie on created_at for deterministic tie-break assertion by snapshot_id
    db = SessionLocal()
    try:
        snaps = db.query(TelemetrySnapshot).filter(TelemetrySnapshot.conversation_id == cid).all()
        assert len(snaps) >= 4
        tie_time = datetime(2026, 1, 1, 0, 0, 0)
        for snap in snaps:
            snap.created_at = tie_time
        db.commit()
    finally:
        db.close()

    recent = client.get(
        f"/v2/conversations/{cid}/telemetry/recent?limit=3&include_actions=false",
        headers=auth_headers,
    )
    assert recent.status_code == 200
    body = recent.json()
    snapshots = body["snapshots"]

    assert len(snapshots) <= 3
    assert any(s["method"] == "ablation_kl" for s in snapshots)

    keys = [(s["created_at"], s["snapshot_id"]) for s in snapshots]
    assert keys == sorted(keys, reverse=True)

    for s in snapshots:
        assert s["actions_taken"] == {"rebuilt_context": False, "quarantined_spans": [], "notes": ""}


def test_telemetry_run_groups_recent_ordering_and_metric_preference(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "verbose"})
    cid = c["conversation_id"]

    t = _add_turn(client, auth_headers, cid, "user", "networking baseline", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "check traces", thread_hint="networking")
    _segment(client, auth_headers, cid)

    r1 = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "networking baseline", "mode": "verbose"},
        headers=auth_headers,
    )
    assert r1.status_code == 200
    r2 = client.post(
        f"/v2/conversations/{cid}/telemetry",
        json={"turn_id": t["turn_id"], "query": "networking baseline again", "mode": "verbose"},
        headers=auth_headers,
    )
    assert r2.status_code == 200

    # force equal created_at_max across groups to validate run_group_id tie-break
    db = SessionLocal()
    try:
        snaps = db.query(TelemetrySnapshot).filter(TelemetrySnapshot.conversation_id == cid).all()
        tie_time = datetime(2026, 1, 2, 0, 0, 0)
        for snap in snaps:
            snap.created_at = tie_time
        db.commit()
    finally:
        db.close()

    rr = client.get(f"/v2/conversations/{cid}/telemetry/run_groups/recent", headers=auth_headers)
    assert rr.status_code == 200
    run_groups = rr.json()["run_groups"]
    assert len(run_groups) >= 2

    keys = [(g["created_at_max"], g["run_group_id"]) for g in run_groups]
    assert keys == sorted(keys, reverse=True)

    g0 = run_groups[0]
    assert g0["has_proxy"] is True
    assert g0["has_ablation"] is True

    detail = client.get(
        f"/v2/conversations/{cid}/telemetry/run_groups/{g0['run_group_id']}",
        headers=auth_headers,
    )
    assert detail.status_code == 200
    snaps = detail.json()["snapshots"]
    ablation = next(s for s in snaps if s["method"] == "ablation_kl")

    assert abs(g0["Coff"] - float(ablation["metrics"]["off_thread_coupling_Coff"])) < 1e-9
    assert abs(g0["H"] - float(ablation["metrics"]["influence_entropy_H"])) < 1e-9


def test_telemetry_latest_matches_first_recent_with_tie_break(client, auth_headers):
    c = _create_conversation(client, auth_headers, settings={"telemetry_mode": "verbose"})
    cid = c["conversation_id"]

    t = _add_turn(client, auth_headers, cid, "user", "networking diagnostics", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "assistant", "collect traces", thread_hint="networking")
    _segment(client, auth_headers, cid)

    for q in ["networking diagnostics one", "networking diagnostics two"]:
        r = client.post(
            f"/v2/conversations/{cid}/telemetry",
            json={"turn_id": t["turn_id"], "query": q, "mode": "verbose"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    # force all snapshots to the same timestamp so ordering relies on snapshot_id tie-break.
    db = SessionLocal()
    try:
        snaps = db.query(TelemetrySnapshot).filter(TelemetrySnapshot.conversation_id == cid).all()
        tie_time = datetime(2026, 1, 3, 0, 0, 0)
        for snap in snaps:
            snap.created_at = tie_time
        db.commit()
    finally:
        db.close()

    recent = client.get(
        f"/v2/conversations/{cid}/telemetry/recent?limit=1",
        headers=auth_headers,
    )
    assert recent.status_code == 200
    recent_first = recent.json()["snapshots"][0]

    latest = client.get(
        f"/v2/conversations/{cid}/telemetry/latest",
        headers=auth_headers,
    )
    assert latest.status_code == 200
    latest_snaps = latest.json()["snapshots"]
    assert len(latest_snaps) >= 1

    # invariant: /latest resolves to the same top snapshot as /recent limit=1
    assert latest_snaps[0]["snapshot_id"] == recent_first["snapshot_id"]
    assert latest_snaps[0]["run_group_id"] == recent_first["run_group_id"]

    keys = [(s["created_at"], s["snapshot_id"]) for s in latest_snaps]
    assert keys == sorted(keys, reverse=True)
