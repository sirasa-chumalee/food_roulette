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
    conn.commit()
