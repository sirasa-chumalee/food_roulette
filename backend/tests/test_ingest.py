"""The data pipeline: right row counts, referential integrity, safe to re-run."""
from __future__ import annotations

import sqlite3

import pytest

from app import config, db, ingest

EXPECTED_RESTAURANTS = 50
EXPECTED_MENU_ITEMS = 1250


def test_row_counts(test_db):
    summary = test_db["summary"]
    assert summary["restaurants"] == EXPECTED_RESTAURANTS
    assert summary["menu_items"] == EXPECTED_MENU_ITEMS


def test_no_orphan_menu_items(test_db):
    assert test_db["summary"]["orphan_menu_items"] == 0


def test_foreign_keys_are_enforced(conn):
    """A menu item pointing at a missing restaurant must be rejected, not stored."""
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO menu_items (id, restaurant_id, name_th) VALUES (?, ?, ?);",
            (999_999, "does_not_exist", "ghost"),
        )


def test_reingest_is_idempotent_and_keeps_user_data(tmp_path):
    """Re-running ingest with updated JSON must not wipe users or history."""
    db_path = tmp_path / "reingest.db"
    conn = db.connect(db_path)
    try:
        ingest.ingest(conn, config.DATA_DIR)
        conn.execute(
            "INSERT INTO users (id, display_name, created_at) VALUES (?, ?, ?);",
            ("keep_me", "regression", "2026-07-28T00:00:00Z"),
        )
        conn.commit()

        second = ingest.ingest(conn, config.DATA_DIR)

        assert second["restaurants"] == EXPECTED_RESTAURANTS
        assert second["menu_items"] == EXPECTED_MENU_ITEMS
        survivors = conn.execute("SELECT COUNT(*) FROM users WHERE id = 'keep_me';").fetchone()[0]
        assert survivors == 1
    finally:
        conn.close()
