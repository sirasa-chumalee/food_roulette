"""Ingest: `description` column is populated from restaurants.json."""

import json
import sqlite3

import pytest

from app import db, ingest


def _make_fixture(tmp_path):
    """A minimal description-bearing restaurants.json + an empty menu file."""
    restaurants = [
        {
            "id": "tu_place_1",
            "google_place_id": "ChIJabc123",
            "name_th": "Swan Lake",
            "name_en": None,
            "latitude": 14.0,
            "longitude": 100.0,
            "price_band": None,
            "is_halal_certified": 0,
            "has_parking": 2,
            "description": "Quiet lakeside cafe known for hand-dripped coffee.",
        },
        {
            "id": "tu_place_2",
            "google_place_id": "ChIJdef456",
            "name_th": "Riverside Noodle",
            "name_en": None,
            "latitude": 13.9,
            "longitude": 100.1,
            "price_band": None,
            "is_halal_certified": 0,
            "has_parking": 2,
            # deliberately no "description" key — must become NULL, not crash
        },
    ]
    (tmp_path / "restaurants.json").write_text(json.dumps(restaurants), encoding="utf-8")
    (tmp_path / "menu_items.json").write_text("[]", encoding="utf-8")


def test_ingest_populates_description(tmp_path):
    _make_fixture(tmp_path)
    conn = db.connect(tmp_path / "test.db")
    try:
        ingest.ingest(conn, tmp_path)
        row = conn.execute(
            "SELECT description FROM restaurants WHERE id = ?;", ("tu_place_1",)
        ).fetchone()
        assert row["description"] == (
            "Quiet lakeside cafe known for hand-dripped coffee."
        )
    finally:
        conn.close()


def test_missing_description_becomes_null(tmp_path):
    _make_fixture(tmp_path)
    conn = db.connect(tmp_path / "test.db")
    try:
        ingest.ingest(conn, tmp_path)
        row = conn.execute(
            "SELECT description FROM restaurants WHERE id = ?;", ("tu_place_2",)
        ).fetchone()
        assert row["description"] is None
    finally:
        conn.close()