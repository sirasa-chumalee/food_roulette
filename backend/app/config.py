"""Central paths & settings for the backend.

All values can be overridden with environment variables so the same code runs on
a teammate's laptop, in CI, or in a container without edits.
"""
from __future__ import annotations

import os
from pathlib import Path

# backend/app/config.py -> backend/ -> repo root
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

# Location of the source-of-truth JSON files (default: repo root).
DATA_DIR = Path(os.environ.get("FR_DATA_DIR", REPO_ROOT))
RESTAURANTS_JSON = DATA_DIR / "restaurants.json"
MENU_ITEMS_JSON = DATA_DIR / "menu_items.json"

# SQLite database file.
DB_PATH = Path(os.environ.get("FR_DB_PATH", BACKEND_DIR / "food_roulette.db"))

# Schema DDL.
SCHEMA_SQL = BACKEND_DIR / "schema.sql"

# Browser origins allowed to call this API. The Android emulator and a physical
# device don't send an Origin header at all, so this only matters for Flutter
# web / DevTools — "*" is fine for local dev and is tightened in deployment.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("FR_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
