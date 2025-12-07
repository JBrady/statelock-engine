from fastapi.testclient import TestClient
from main import app
import pytest
import shutil
import os
from app.core.database import Database
from app.core.config import settings

# Override the DB path for testing
TEST_DB_PATH = "./test_chroma_db"

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Setup: Configure ChromaDB to use a test path
    original_path = settings.CHROMA_DB_PATH
    settings.CHROMA_DB_PATH = TEST_DB_PATH

    # Reset singleton to ensure it picks up the new path
    Database._client = None
    Database._collection = None

    yield

    # Teardown: Remove test DB directory
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)

    # Restore original settings
    settings.CHROMA_DB_PATH = original_path
    Database._client = None
    Database._collection = None

@pytest.fixture
def client():
    return TestClient(app)

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to StateLock Engine API v2"}

def test_add_and_query_memory(client):
    # 1. Add
    payload = {
        "content": "The sky is blue.",
        "name": "Fact 1",
        "session_id": "test_session_1",
        "tags": ["nature", "color"]
    }
    response = client.post("/memories/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == payload["content"]
    assert data["session_id"] == "test_session_1"
    block_id = data["id"]

    # 2. Query
    query_payload = {
        "query_text": "What color is the sky?",
        "session_id": "test_session_1",
        "top_k": 1
    }
    response = client.post("/memories/query", json=query_payload)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    assert results[0]["id"] == block_id

    # 3. Query Wrong Session
    query_payload_wrong = {
        "query_text": "What color is the sky?",
        "session_id": "wrong_session",
        "top_k": 1
    }
    response = client.post("/memories/query", json=query_payload_wrong)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 0

    # 4. Cleanup
    client.delete(f"/memories/{block_id}")

def test_session_isolation(client):
    # Add memory to Session A
    client.post("/memories/", json={"content": "Secret A", "session_id": "A"})
    # Add memory to Session B
    client.post("/memories/", json={"content": "Secret B", "session_id": "B"})

    # List Session A
    resp_a = client.get("/memories/?session_id=A")
    assert len(resp_a.json()) >= 1
    for item in resp_a.json():
        assert item["session_id"] == "A"
        assert item["content"] != "Secret B"

    # Cleanup
    client.delete("/memories/session/A")
    client.delete("/memories/session/B")
