"""Ingest restaurants.json + menu_items.json into SQLite.

Design notes (docs/DESIGN.md §3):
  * The two JSON files are the normalized source of truth: restaurants is the
    dimension table, menu_items the fact table, joined on restaurant_id.
  * Idempotent & swappable: re-running rebuilds ONLY the reference tables
    (restaurants, menu_items) and leaves user data (users, user_preferences,
    action_history) untouched, so a teammate can drop in updated JSON without
    losing history.
  * Foreign keys are enforced; menu_items rows whose restaurant_id is unknown
    would violate the FK and abort the transaction.

Run from the backend/ directory:
    python -m app.ingest
Options:
    python -m app.ingest --db /tmp/test.db --data-dir /path/to/json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from . import config, db, pricing

# Column order used for the INSERT statements. Kept explicit so a change to the
# JSON key order never silently shifts values into the wrong column.
RESTAURANT_COLUMNS = [
    "id",
    "google_place_id",
    "name_th",
    "name_en",
    "latitude",
    "longitude",
    "price_band",
    "is_halal_certified",
    "has_parking",
]

MENU_COLUMNS = [
    "id",
    "restaurant_id",
    "name_th",
    "name_en",
    "category",
    "price_thb",
    "spicy_level",
    "confidence",
    "crustaceans",
    "fish",
    "milk",
    "eggs",
    "peanuts",
    "tree_nuts",
    "wheat",
    "soy",
    "sesame",
    "molluscs",
    "contains_meat",
    "contains_pork",
    "contains_beef",
    "contains_alcohol",
    "contains_pungent_veg",
    "is_vegetarian",
    "is_vegan",
    "is_pescatarian",
    "is_jay",
]

# menu_items.json stores these as JSON booleans; SQLite has no bool type, so we
# coerce to 0/1 integers on the way in.
BOOL_COLUMNS = {"is_vegetarian", "is_vegan", "is_pescatarian", "is_jay"}


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing data file: {path}\n"
            "Set FR_DATA_DIR or pass --data-dir to point at the folder that "
            "contains restaurants.json and menu_items.json."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path.name} must be a JSON array, got {type(data).__name__}")
    return data


def _row_tuple(record: dict, columns: list[str]) -> tuple:
    values = []
    for col in columns:
        val = record.get(col)
        if col in BOOL_COLUMNS and isinstance(val, bool):
            val = int(val)
        values.append(val)
    return tuple(values)


def ingest(conn: sqlite3.Connection, data_dir: Path) -> dict:
    """Load both JSON files into the connection. Returns a summary dict."""
    restaurants = _load_json(data_dir / config.RESTAURANTS_JSON.name)
    menu_items = _load_json(data_dir / config.MENU_ITEMS_JSON.name)

    db.init_schema(conn)

    # Rebuild reference tables only. FK cascade on menu_items is redundant here
    # because we clear menu_items first, but we keep the order explicit.
    conn.execute("DELETE FROM menu_items;")
    conn.execute("DELETE FROM restaurants;")

    conn.executemany(
        f"INSERT INTO restaurants ({', '.join(RESTAURANT_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in RESTAURANT_COLUMNS)});",
        [_row_tuple(r, RESTAURANT_COLUMNS) for r in restaurants],
    )
    conn.executemany(
        f"INSERT INTO menu_items ({', '.join(MENU_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in MENU_COLUMNS)});",
        [_row_tuple(m, MENU_COLUMNS) for m in menu_items],
    )
    conn.commit()

    # `price_band` arrives NULL for all 50 rows, so we derive it here — offline,
    # from the menu we just loaded, rather than at request time (DESIGN §7).
    priced = pricing.derive_price_bands(conn)

    # Integrity check: no menu row should reference a missing restaurant.
    orphans = conn.execute(
        "SELECT COUNT(*) FROM menu_items m "
        "LEFT JOIN restaurants r ON m.restaurant_id = r.id "
        "WHERE r.id IS NULL;"
    ).fetchone()[0]

    return {
        "restaurants": conn.execute("SELECT COUNT(*) FROM restaurants;").fetchone()[0],
        "menu_items": conn.execute("SELECT COUNT(*) FROM menu_items;").fetchone()[0],
        "orphan_menu_items": orphans,
        "price_bands_derived": priced,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest JSON data into SQLite.")
    parser.add_argument("--db", type=Path, default=config.DB_PATH, help="SQLite file path")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=config.DATA_DIR,
        help="Folder containing restaurants.json and menu_items.json",
    )
    args = parser.parse_args()

    conn = db.connect(args.db)
    try:
        summary = ingest(conn, args.data_dir)
    finally:
        conn.close()

    print(f"Ingested into {args.db}")
    print(f"  restaurants : {summary['restaurants']}")
    print(f"  menu_items  : {summary['menu_items']}")
    print(f"  price bands : {summary['price_bands_derived']} derived from menu medians")
    if summary["orphan_menu_items"]:
        raise SystemExit(
            f"  ERROR: {summary['orphan_menu_items']} menu_items reference a "
            "missing restaurant (foreign-key integrity failed)."
        )
    print("  FK integrity: OK (no orphan menu_items)")


if __name__ == "__main__":
    main()
