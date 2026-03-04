from __future__ import annotations

from app.config import resolve_database_url


def test_resolve_database_url_relative_sqlite_path(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    db_url, sqlite_path = resolve_database_url(db_url_env=None, sqlite_path_env="./data/statelock_v2.db")

    expected_path = (tmp_path / "data" / "statelock_v2.db").resolve()
    assert sqlite_path == str(expected_path)
    assert db_url == f"sqlite:///{expected_path}"
    assert expected_path.parent.exists()


def test_resolve_database_url_from_sqlite_db_url(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    db_url, sqlite_path = resolve_database_url(db_url_env="sqlite:///./mydb/app.db", sqlite_path_env=None)

    expected_path = (tmp_path / "mydb" / "app.db").resolve()
    assert sqlite_path == str(expected_path)
    assert db_url == f"sqlite:///{expected_path}"
    assert expected_path.parent.exists()


def test_resolve_database_url_non_sqlite_passthrough():
    url = "postgresql://user:pass@localhost:5432/db"
    db_url, sqlite_path = resolve_database_url(db_url_env=url, sqlite_path_env="./ignored.db")

    assert db_url == url
    assert sqlite_path is None
