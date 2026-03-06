from __future__ import annotations

import atexit
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_TEST_DB_DIR = TemporaryDirectory(prefix="statelock-obs-tests-")
atexit.register(_TEST_DB_DIR.cleanup)
_TEST_DB_PATH = Path(_TEST_DB_DIR.name) / "test_statelock.db"

os.environ.setdefault("STATELOCK_DB_URL", f"sqlite:///{_TEST_DB_PATH}")
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
