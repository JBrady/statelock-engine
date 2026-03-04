from __future__ import annotations


def _create_conversation(client, headers):
    r = client.post("/v2/conversations", json={"title": "demo"}, headers=headers)
    assert r.status_code == 200


def test_homepage_renders_onboarding_panel(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "What is this tool?" in r.text


def test_homepage_shows_welcome_when_no_conversations(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Welcome to StateLock" in r.text


def test_homepage_hides_welcome_when_conversation_exists(client, auth_headers):
    _create_conversation(client, auth_headers)
    r = client.get("/")
    assert r.status_code == 200
    assert "Welcome to StateLock" not in r.text
