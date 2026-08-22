-- Food Roulette — SQLite schema (Phase 1)
-- See docs/DESIGN.md §3. Foreign keys must be enabled per-connection with
-- `PRAGMA foreign_keys = ON;` (SQLite defaults it off).

-- ---------------------------------------------------------------------------
-- Reference data (re-created on every ingest from the JSON source of truth)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS restaurants (
    id                 TEXT PRIMARY KEY,          -- tu_place_N (matches JSON)
    google_place_id    TEXT,                      -- already resolved in restaurants.json
    name_th            TEXT,
    name_en            TEXT,
    latitude           REAL,
    longitude          REAL,
    price_band         TEXT,                      -- null today; derivable from menu prices
        is_halal_certified INTEGER,                   -- 0 = placeholder; do NOT filter on yet
        has_parking        INTEGER,                   -- 2 = "unknown" sentinel
        description        TEXT,                      -- human-written, shown on detail; SEARCH signal only

    -- Cached Google Places enrichment (M4; null until synced)
        rating              REAL,
        user_rating_count   INTEGER,
        places_display_name TEXT,
        places_address      TEXT,
        photo_refs_json     TEXT,
        hours_json          TEXT,
        reviews_json        TEXT,
        places_synced_at    TEXT
    );

CREATE TABLE IF NOT EXISTS menu_items (
    id                   INTEGER PRIMARY KEY,     -- global id from menu_items.json
    restaurant_id        TEXT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name_th              TEXT,
    name_en              TEXT,
    category             TEXT,
    price_thb            REAL,
    spicy_level          INTEGER,
    confidence           TEXT,                    -- 'high' | 'low'

    -- Raw allergen flags (0/1)
    crustaceans          INTEGER,
    fish                 INTEGER,
    milk                 INTEGER,
    eggs                 INTEGER,
    peanuts              INTEGER,
    tree_nuts            INTEGER,
    wheat                INTEGER,
    soy                  INTEGER,
    sesame               INTEGER,
    molluscs             INTEGER,

    -- Raw dietary flags (0/1)
    contains_meat        INTEGER,
    contains_pork        INTEGER,
    contains_beef        INTEGER,
    contains_alcohol     INTEGER,
    contains_pungent_veg INTEGER,

    -- Pre-derived diet booleans (from menu_items.json)
    is_vegetarian        INTEGER,
    is_vegan             INTEGER,
    is_pescatarian       INTEGER,
    is_jay               INTEGER
);

CREATE INDEX IF NOT EXISTS idx_menu_rid        ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_confidence ON menu_items(confidence);

-- ---------------------------------------------------------------------------
-- User data (persists across re-ingests — NEVER dropped by ingest.py)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    display_name TEXT,
    created_at   TEXT
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id   TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    hard_json TEXT,   -- {allergens:[], religion, intolerances:[]}
    soft_json TEXT    -- {diet_style, spicy_tolerance, price_tier, facilities}
);

CREATE TABLE IF NOT EXISTS action_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT,
    user_id       TEXT REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id TEXT,
    action_type   TEXT,   -- IMPRESSION | CLICK | SPIN | REJECTION
    ts            TEXT,
    context       TEXT
);

CREATE INDEX IF NOT EXISTS idx_history_session ON action_history(session_id);
CREATE INDEX IF NOT EXISTS idx_history_user    ON action_history(user_id);

-- M3: fast lookup of session-scoped rejection feedback used by ranking.
CREATE INDEX IF NOT EXISTS idx_history_session_action_restaurant
    ON action_history(session_id, action_type, restaurant_id);
