from __future__ import annotations

from datetime import datetime, timedelta

from app.db.models import Span
from app.db.session import SessionLocal


def _create_conversation(client, headers):
    r = client.post("/v2/conversations", json={"title": "conv"}, headers=headers)
    assert r.status_code == 200
    return r.json()["conversation_id"]


def _add_turn(client, headers, cid, speaker, text, thread_hint=None):
    r = client.post(
        f"/v2/conversations/{cid}/turns",
        json={"speaker": speaker, "text": text, "thread_hint": thread_hint},
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()


def test_spans_list_filters_and_include_quarantined(client, auth_headers):
    cid = _create_conversation(client, auth_headers)
    _add_turn(client, auth_headers, cid, "user", "network troubleshooting", thread_hint="networking")
    _add_turn(client, auth_headers, cid, "user", "cosmology inflation", thread_hint="cosmology")
    seg = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=auth_headers)
    assert seg.status_code == 200

    db = SessionLocal()
    try:
        span = db.query(Span).filter(Span.conversation_id == cid, Span.thread_id == "cosmology").first()
        assert span is not None
        span.quarantined_until = datetime.utcnow() + timedelta(minutes=30)
        db.commit()
        q_span_id = span.span_id
    finally:
        db.close()

    r = client.get(
        f"/v2/conversations/{cid}/spans?thread_id=cosmology&include_quarantined=false",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert all(s["span_id"] != q_span_id for s in r.json())

    r2 = client.get(
        f"/v2/conversations/{cid}/spans?thread_id=cosmology&include_quarantined=true",
        headers=auth_headers,
    )
    assert r2.status_code == 200
    assert any(s["span_id"] == q_span_id for s in r2.json())


def test_manual_unquarantine_restores_eligibility(client, auth_headers):
    cid = _create_conversation(client, auth_headers)
    _add_turn(client, auth_headers, cid, "user", "network troubleshooting", thread_hint="networking")
    seg = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=auth_headers)
    assert seg.status_code == 200

    db = SessionLocal()
    try:
        span = db.query(Span).filter(Span.conversation_id == cid).first()
        assert span is not None
        span.quarantined_until = datetime.utcnow() + timedelta(minutes=30)
        sid = span.span_id
        db.commit()
    finally:
        db.close()

    r = client.post(f"/v2/conversations/{cid}/spans/{sid}/unquarantine", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["unquarantined"] is True

    spans = client.get(f"/v2/conversations/{cid}/spans?include_quarantined=false", headers=auth_headers).json()
    assert any(s["span_id"] == sid for s in spans)

    wc = client.post(
        f"/v2/conversations/{cid}/working_context",
        json={"query": "network troubleshooting", "max_context_tokens": 500},
        headers=auth_headers,
    )
    assert wc.status_code == 200
    assert sid in wc.json()["selected_span_ids"]
