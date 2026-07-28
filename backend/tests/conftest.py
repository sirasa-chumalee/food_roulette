"""Shared test fixtures.

Every test in this suite runs against a **throwaway SQLite file** in pytest's
tmp directory. Nothing here may touch a developer's real
`backend/food_roulette.db` — the autouse fixture below guarantees that by
repointing `config.DB_PATH` before any app code opens a connection
(`db.connect()` reads that attribute at call time, not at import time).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config, db, ingest
from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def test_db(tmp_path_factory) -> dict:
    """Build a fresh DB from the real JSON files, once per test session."""
    db_path = tmp_path_factory.mktemp("food_roulette") / "test.db"
    original = config.DB_PATH
    config.DB_PATH = db_path

    conn = db.connect(db_path)
    try:
        summary = ingest.ingest(conn, config.DATA_DIR)
    finally:
        conn.close()

    yield {"path": db_path, "summary": summary}

    config.DB_PATH = original


@pytest.fixture(autouse=True)
def _use_test_db(test_db) -> None:
    """Applied to every test, so no test can accidentally hit the real DB."""
    return None


@pytest.fixture()
def conn(test_db):
    connection = db.connect(test_db["path"])
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture()
def client(test_db) -> TestClient:
    # Context-managed so the app's lifespan (schema init) actually runs.
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture()
def user_id(client) -> str:
    """A registered user — most endpoints need one to exist."""
    response = client.post("/auth/session", json={"display_name": "pytest"})
    assert response.status_code == 201
    return response.json()["user_id"]
