# Food Roulette 🍜

An AI restaurant-picker for the **Thammasat University** area. Users describe what
they feel like eating (in Thai or English) and the app recommends nearby restaurants
while strictly respecting **allergies, religious, and dietary constraints**.

This repo is a **dual project**:

```
food_roulette/
├── lib/  android/  ios/  …      # Flutter client (Android target)
├── restaurants.json            # ← mock data: 50 TU restaurants  (source of truth)
├── menu_items.json             # ← mock data: 1250 menu items    (source of truth)
├── docs/DESIGN.md              # architecture blueprint — READ THIS FIRST
└── backend/                    # Python + FastAPI backend
    ├── app/                    # config, db, ingest, main (API)
    ├── schema.sql              # SQLite schema (with foreign keys)
    └── requirements.txt
```

> **Current status: Phase 1** — data pipeline + minimal API. The recommendation
> filter, Gemini chat, Google Places enrichment, and the roulette widget come in
> later phases. See `docs/DESIGN.md §10` for the roadmap.

---

## Backend — local setup (Phase 1)

Everything below runs from the **`backend/`** folder. Requires **Python 3.11+**
(3.13 tested). No API keys are needed for Phase 1.

### 1. Create and activate a virtual environment

```bash
cd backend
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

Your shell prompt should now be prefixed with `(.venv)`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Load the mock data into SQLite

This reads `restaurants.json` + `menu_items.json` (from the repo root) and builds a
local `food_roulette.db`:

```bash
python -m app.ingest
```

Expected output:

```
Ingested into .../backend/food_roulette.db
  restaurants : 50
  menu_items  : 1250
  FK integrity: OK (no orphan menu_items)
```

The script is **idempotent** — re-run it any time the JSON files change. It rebuilds
only the `restaurants` / `menu_items` tables and **preserves** user data
(`users`, `user_preferences`, `action_history`).

### 4. Run the API server

```bash
uvicorn app.main:app --reload
```

Then open:

| URL | What |
|-----|------|
| http://127.0.0.1:8000/health | status + row counts (confirms ingest worked) |
| http://127.0.0.1:8000/restaurants | all 50 restaurants + menu counts |
| http://127.0.0.1:8000/restaurants/tu_place_1 | one restaurant + its full menu |
| http://127.0.0.1:8000/docs | interactive Swagger UI |

A healthy response looks like:

```json
{"status":"ok","version":"0.1.0","restaurants":50,"menu_items":1250}
```

### One-liner (after steps 1 & 2)

```bash
python -m app.ingest && uvicorn app.main:app --reload
```

---

## Configuration (optional)

All overridable via environment variables — defaults work out of the box:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FR_DATA_DIR` | repo root | folder holding `restaurants.json` / `menu_items.json` |
| `FR_DB_PATH` | `backend/food_roulette.db` | SQLite file location |

Example (use a throwaway DB):

```bash
FR_DB_PATH=/tmp/fr.db python -m app.ingest
```

---

## Data model (quick reference)

Two normalized tables joined by `restaurant_id` (full DDL in `backend/schema.sql`):

- **`restaurants`** — one row per venue: `id`, `google_place_id`, `name_th`,
  `latitude`/`longitude`, plus placeholders to be enriched later (`price_band`,
  `is_halal_certified`, `has_parking`) and cached Google Places fields.
- **`menu_items`** — 25 per restaurant: name, price, `spicy_level`, raw allergen &
  dietary flags, a `confidence` field, and pre-derived diet booleans
  (`is_vegetarian`, `is_vegan`, `is_pescatarian`, `is_jay`).

Foreign keys are enforced (`PRAGMA foreign_keys = ON` on every connection), so a
menu item can never point at a missing restaurant.

---

## Flutter client

Standard Flutter app at the repo root (Android target). Requires the Flutter SDK.

```bash
flutter pub get
flutter run
```

The client is a fresh scaffold today; UI work begins once the backend recommendation
endpoints land. See `docs/DESIGN.md §9` for the planned Riverpod structure and screens.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: fastapi` | activate the venv, then `pip install -r requirements.txt` |
| `Missing data file: restaurants.json` | run from `backend/`, or set `FR_DATA_DIR` to the folder with the JSON files |
| `/health` shows `restaurants: 0` | you haven't run `python -m app.ingest` yet |
| port 8000 in use | `uvicorn app.main:app --port 8001` |
