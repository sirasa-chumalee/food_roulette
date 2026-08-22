"""SQLite connection helpers.

Every connection enables foreign-key enforcement (SQLite leaves it OFF by
default) and returns rows as dict-like ``sqlite3.Row`` objects.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with foreign keys ON and Row access."""
    conn = sqlite3.connect(db_path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables/indexes if they do not already exist (idempotent)."""
    conn.executescript(config.SCHEMA_SQL.read_text(encoding="utf-8"))
    _migrate_places_columns(conn)
    conn.commit()


# Columns added after the initial schema was committed. `CREATE TABLE IF NOT
# EXISTS` does nothing to a table that already exists, so a developer's existing
# `food_roulette.db` needs them ADDed rather than recreated. This is the same
# drift-avoiding habit as `ingest.py` rebuilding only reference tables — user
# data must survive a schema bump without a manual `rm db`.
_PLACES_MIGRATIONS: dict[str, str] = {
    "user_rating_count": "INTEGER",
    "places_display_name": "TEXT",
    "places_address": "TEXT",
    "photo_refs_json": "TEXT",
    "hours_json": "TEXT",
    "reviews_json": "TEXT",
    # Human-written description (search/display signal). Not Places, but it's
    # added the same lazy way for an existing dev DB.
    "description": "TEXT",
}


def _migrate_places_columns(conn: sqlite3.Connection) -> None:
    """Add Places cache columns to a `restaurants` table created pre-M4."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(restaurants);")}
    for column, ddl_type in _PLACES_MIGRATIONS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE restaurants ADD COLUMN {column} {ddl_type};")
