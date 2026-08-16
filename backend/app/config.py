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

# --- Google Places (M4) ------------------------------------------------------
# Unset is a normal, supported state: `rating`/`photo_url`/reviews/hours all
# render as nulls and the app keeps working, just plainer (DESIGN §7). The key
# lives only in the backend; the Flutter client never sees it.
PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

# Modern Places API (v1) base URLs. Place Details is keyed by the
# `google_place_id` already present in restaurants.json — no name search, no
# geocoding (DESIGN §7). A photo is fetched from a `name` returned by Details,
# so the client only ever holds a (stateless, keyless) backend URL.
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
PLACES_PHOTO_MEDIA_URL = "https://places.googleapis.com/v1/{photo_name}/media"

# Places is a display layer, not a safety path, so a slow/failed lookup just
# means nulls — a shorter deadline than Gemini is the right trade.
PLACES_TIMEOUT_MS = int(os.environ.get("PLACES_TIMEOUT_MS", "8000"))

# A cached enrichment is reused until it's this old; only then is it refetched
# on the next request (lazy). Failures keep whatever we already have.
PLACES_CACHE_TTL_HOURS = int(os.environ.get("PLACES_CACHE_TTL_HOURS", "168"))  # 7 days

# Cap on the proxied photo dimension (maxWidthPx / maxHeightPx sent to Places).
# Keeps the payload reasonable for mobile card images.
PLACES_MAX_PHOTO_WIDTH = int(os.environ.get("PLACES_MAX_PHOTO_WIDTH", "600"))
