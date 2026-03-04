from __future__ import annotations

import os

os.environ.setdefault("STATELOCK_DB_URL", "sqlite:///./test_statelock.db")
os.environ.setdefault("STATELOCK_API_KEY", "dev-key")

import pytest
from fastapi.testclient import TestClient

from app.db import models  # noqa: F401
from app.db.session import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer dev-key"}
