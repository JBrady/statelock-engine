import os
import shutil

import pytest
from fastapi.testclient import TestClient

import app.services.embedder as embedder_module
from app.core.config import settings
from app.core.database import Database
from main import app

TEST_DB_PATH = "./test_chroma_db"


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    original_path = settings.CHROMA_DB_PATH
    original_provider = settings.EMBEDDING_PROVIDER
    original_auth_required = settings.AUTH_REQUIRED
    original_api_key = settings.STATELOCK_API_KEY

    settings.CHROMA_DB_PATH = TEST_DB_PATH
    settings.EMBEDDING_PROVIDER = "hash"
    settings.AUTH_REQUIRED = False
    settings.STATELOCK_API_KEY = ""
    Database._client = None
    Database._collection = None
    embedder_module.reset_embedder()

    yield

    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)

    settings.CHROMA_DB_PATH = original_path
    settings.EMBEDDING_PROVIDER = original_provider
    settings.AUTH_REQUIRED = original_auth_required
    settings.STATELOCK_API_KEY = original_api_key
    Database._client = None
    Database._collection = None
    embedder_module.reset_embedder()


@pytest.fixture
def client():
    return TestClient(app)


def test_read_main(client):
    response = client.get("/", headers={"X-Statelock-Version": "client-v1"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "memory-sidecar"
    assert response.headers.get("X-Statelock-Version")
    assert response.headers.get("X-Trace-Id")
    assert response.headers.get("X-Statelock-Version-Requested") == "client-v1"


def test_add_query_and_list_pagination(client):
    payload = {
        "content": "The sky is blue.",
        "name": "Fact 1",
        "session_id": "test_session_1",
        "tags": ["nature", "color"],
    }
    create_res = client.post("/memories/", json=payload)
    assert create_res.status_code == 201
    block_id = create_res.json()["id"]

    query_payload = {
        "query_text": "What color is the sky?",
        "session_id": "test_session_1",
        "top_k": 1,
    }
    query_res = client.post("/memories/query", json=query_payload)
    assert query_res.status_code == 200
    assert len(query_res.json()["results"]) >= 1

    list_res = client.get("/memories/?session_id=test_session_1&limit=1&offset=0")
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert body["total"] >= 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == block_id

    client.delete(f"/memories/{block_id}")


def test_upsert_idempotent_and_hybrid_query(client):
    payload = {
        "external_id": "fact:sky",
        "content": "Sky appears blue due to Rayleigh scattering.",
        "name": "Sky color reason",
        "session_id": "science",
        "tags": ["physics"],
    }
    first = client.post("/memories/upsert", json=payload)
    second = client.post("/memories/upsert", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    hybrid = client.post(
        "/memories/query-hybrid",
        json={
            "query_text": "why is the sky blue",
            "session_id": "science",
            "top_k": 1,
            "candidate_k": 5,
        },
    )
    assert hybrid.status_code == 200
    results = hybrid.json()["results"]
    assert len(results) == 1
    assert "score" in results[0]

    client.delete(f"/memories/{first.json()['id']}")


def test_session_snapshot_and_restore(client):
    sid = "restore_demo"
    client.post("/memories/", json={"content": "A", "session_id": sid, "tags": ["alpha"]})
    client.post("/memories/", json={"content": "B", "session_id": sid, "tags": ["beta"]})

    snap = client.get(f"/memories/session/{sid}/snapshot")
    assert snap.status_code == 200
    snapshot = snap.json()
    assert snapshot["session_id"] == sid
    assert snapshot["total"] >= 2
    memories = snapshot["memories"]

    client.delete(f"/memories/session/{sid}")
    empty = client.get(f"/memories/?session_id={sid}")
    assert empty.status_code == 200
    assert empty.json()["items"] == []

    restore = client.post(
        f"/memories/session/{sid}/restore",
        json={"mode": "append", "memories": memories},
    )
    assert restore.status_code == 200
    assert restore.json()["restored"] >= 2

    restored = client.get(f"/memories/?session_id={sid}")
    assert restored.status_code == 200
    assert len(restored.json()["items"]) >= 2

    client.delete(f"/memories/session/{sid}")


def test_validation_and_error_contract(client):
    bad = client.post("/memories/query", json={"query_text": "", "top_k": 0})
    assert bad.status_code == 422
    body = bad.json()
    assert body["code"] == "validation_error"
    assert "trace_id" in body

    too_long = client.post(
        "/memories/",
        json={
            "content": "x",
            "session_id": "s",
            "tags": ["a" * (settings.API_TAG_MAX_CHARS + 1)],
        },
    )
    assert too_long.status_code == 422
    assert too_long.json()["code"] == "validation_error"


def test_health_and_ready(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_auth_required(client):
    settings.AUTH_REQUIRED = True
    settings.STATELOCK_API_KEY = "test-key"

    missing = client.get("/memories/?limit=1")
    assert missing.status_code == 401
    assert missing.json()["code"] == "unauthorized"

    wrong = client.get("/memories/?limit=1", headers={"X-Statelock-Api-Key": "bad"})
    assert wrong.status_code == 401

    ok = client.get("/memories/?limit=1", headers={"X-Statelock-Api-Key": "test-key"})
    assert ok.status_code == 200

    settings.AUTH_REQUIRED = False
    settings.STATELOCK_API_KEY = ""


def test_insights_endpoints(client):
    client.post(
        "/memories/",
        json={
            "content": "Use local-first fallback policy",
            "session_id": "telegram:chat_1:user_1",
            "tags": ["policy", "fallback"],
        },
    )
    client.post(
        "/memories/",
        json={
            "content": "User prefers concise responses",
            "session_id": "telegram:chat_1:user_1",
            "tags": ["preference"],
        },
    )
    client.post(
        "/memories/",
        json={
            "content": "Todo: add better diagnostics",
            "session_id": "telegram:chat_2:user_2",
            "tags": ["todo"],
        },
    )

    overview = client.get("/stats/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["total_memories"] >= 3
    assert body["total_sessions"] >= 2
    assert "top_tags" in body

    sessions = client.get("/sessions?limit=10&offset=0")
    assert sessions.status_code == 200
    sessions_body = sessions.json()
    assert sessions_body["total"] >= 2
    assert len(sessions_body["items"]) >= 2
    assert "session_id" in sessions_body["items"][0]

    tags = client.get("/tags?limit=10&offset=0")
    assert tags.status_code == 200
    tags_body = tags.json()
    assert tags_body["total"] >= 3
    assert len(tags_body["items"]) >= 3
