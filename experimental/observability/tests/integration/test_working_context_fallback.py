from __future__ import annotations


def _create_conversation(client, headers):
    r = client.post(
        "/v2/conversations",
        json={
            "title": "pinned-low-overlap",
            "settings": {
                "target_thread_mode": "pinned",
                "pinned_thread_id": "networking",
                "max_context_tokens": 250,
            },
        },
        headers=headers,
    )
    assert r.status_code == 200
    return r.json()["conversation_id"]


def _add_turn(client, headers, cid, speaker, text, thread_hint=None):
    r = client.post(
        f"/v2/conversations/{cid}/turns",
        json={"speaker": speaker, "text": text, "thread_hint": thread_hint},
        headers=headers,
    )
    assert r.status_code == 200


def test_pinned_low_overlap_still_returns_evidence_span(client, auth_headers):
    cid = _create_conversation(client, auth_headers)

    for i in range(14):
        _add_turn(
            client,
            auth_headers,
            cid,
            "user" if i % 2 == 0 else "assistant",
            f"network troubleshooting baseline diagnostics segment {i}",
            thread_hint="networking",
        )

    seg = client.post(f"/v2/conversations/{cid}/segment", json={"mode": "incremental"}, headers=auth_headers)
    assert seg.status_code == 200

    wc = client.post(
        f"/v2/conversations/{cid}/working_context",
        json={
            "query": "quantum hummingbird kaleidoscope",
            "target_thread_mode": "pinned",
            "pinned_thread_id": "networking",
            "max_context_tokens": 250,
        },
        headers=auth_headers,
    )
    assert wc.status_code == 200
    body = wc.json()

    assert body["target_thread_id"] == "networking"
    assert len(body["selected_span_ids"]) >= 1
    assert body["token_count_est"] <= 250
