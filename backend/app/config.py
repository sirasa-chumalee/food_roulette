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

# --- Gemini (M2 — chat) -----------------------------------------------------
# No default. An unset key is a normal, supported state: /chat notices it and
# degrades to the plain recommendation path instead of guessing (ROADMAP §4 M2).
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Pinned rather than "latest" because a silently-renamed model is a runtime
# failure with no warning (ROADMAP §6). 2.5 Flash is the model this project
# uses (DESIGN §0) and the one our key is provisioned for.
#
# Worth knowing if you go looking: `client.models.list()` does not return
# gemini-2.5-flash even though calls to it succeed, so an id missing from that
# listing is not evidence it's unavailable — try it before replacing it.
# The Lite tier DESIGN suggested for extraction is retired for new keys, so both
# steps share the one model.
GEMINI_EXTRACT_MODEL = os.environ.get("GEMINI_EXTRACT_MODEL", "gemini-2.5-flash")
GEMINI_NARRATE_MODEL = os.environ.get("GEMINI_NARRATE_MODEL", "gemini-2.5-flash")

# Gemini's own default is generous; chat is user-facing, so we'd rather fall
# back to the safe recommendation path than leave someone watching a spinner.
# 10s is the floor the API accepts — anything lower is rejected outright.
GEMINI_TIMEOUT_MS = int(os.environ.get("GEMINI_TIMEOUT_MS", "15000"))
