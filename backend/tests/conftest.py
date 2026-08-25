"""Shared test fixtures.

Every test in this suite runs against a **throwaway SQLite file** in pytest's
tmp directory. Nothing here may touch a developer's real
`backend/food_roulette.db` — the autouse fixture below guarantees that by
repointing `config.DB_PATH` before any app code opens a connection
(`db.connect()` reads that attribute at call time, not at import time).
"""
from __future__ import annotations

import os
import uuid

# Must be set BEFORE importing app.main: auth.py fails fast (module-level
# raise) when JWT_SECRET_KEY is unset, so we can never test against the
# publicly-known default secret an attacker already knows.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-not-for-prod-0123456789abcdef")

import pytest
from fastapi.testclient import TestClient

from app import auth as app_auth
from app import config, db, ingest
from app.main import app as fastapi_app


def _register(client, email: str, password: str = "hunter22", display_name: str = "pytest") -> dict:
    """Register a throwaway user through the real /auth/register."""
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client, email: str, password: str = "hunter22") -> dict:
    """Log in and return the access token."""
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def bearer(token: str) -> dict:
    """Authorization header dict for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


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


def _make_user(client) -> dict:
    """Register + log in a fresh throwaway user; returns id, token, headers."""
    email = f"pytest-{uuid.uuid4().hex}@test.com"
    created = _register(client, email)
    user_id = created["id"]
    token = _login(client, email)["access_token"]
    return {
        "user_id": user_id,
        "email": email,
        "token": token,
        "headers": bearer(token),
    }


@pytest.fixture()
def user(client) -> dict:
    """A registered + logged-in user: `user_id`, `token` and ready-made
    `headers` (an Authorization: Bearer *** for driving protected routes."""
    return _make_user(client)


@pytest.fixture()
def another_user(client) -> dict:
    """A second, distinct registered+logged-in user.

    Needed by tests that must prove one account's data is invisible to another
    (`test_history_isolated_by_user`): requesting the same `user` fixture twice
    would hand back the same account, so this fixture exists to mint a second one.
    """
    return _make_user(client)


@pytest.fixture()
def user_id(user) -> str:
    """Back-compat alias: the registered user's id alone."""
    return user["user_id"]


@pytest.fixture()
def mint(client):
    """Mint a bearer header for an arbitrary user_id WITHOUT touching the DB.

    Needed by tests that exercise the "token points at a user who doesn't
    exist in the DB" 404 path — the dependency only decodes the JWT, the route
    then refuses to find the account. The token is signed with the test secret,
    so it satisfies the auth layer just like a real client token would.
    """

    def _mint(user_id: str) -> dict:
        return bearer(app_auth.create_access_token(user_id))

    return _mint