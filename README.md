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
├── docs/api/                   # the frozen API contract: openapi.yaml + fixtures
├── ROADMAP.md                  # who builds what, in what order
└── backend/                    # Python + FastAPI backend
    ├── app/                    # config, db, ingest, main (API)
    ├── tests/                  # pytest — runs on a throwaway DB
    ├── tools/                  # contract + fixture generator
    ├── schema.sql              # SQLite schema (with foreign keys)
    └── requirements.txt
```

> **Current status: M0 complete** — both halves run locally and the API contract
> is committed. The safety filter's test suite (M1), Gemini chat (M2), history
> (M3), Places (M4) and the roulette widget (M5) follow. See `ROADMAP.md §4`.

---

## Backend — local setup

Everything below runs from the **`backend/`** folder. Requires **Python 3.11+**
(3.13 tested). No API keys are needed before M4.

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

# ...or, if you'll be running the tests (recommended for backend devs):
pip install -r requirements.txt -r requirements-dev.txt
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
uvicorn app.main:app --reload --host 0.0.0.0
```

**`--host 0.0.0.0` matters.** The default (`127.0.0.1`) is unreachable from an
Android emulator or a phone — see [Reaching the backend from Flutter](#reaching-the-backend-from-flutter).

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

If `restaurants` is `0`, you skipped step 3.

### 5. Run the tests

```bash
pytest
```

24 tests, well under a second. They build their **own throwaway database** in a
temp folder — running them never touches your local `food_roulette.db`.

Anything touching the safety filter (`filter.py` / `ranking.py`, M1 onward) must
have tests, and they gate merges. This is the medical-safety path — see
`ROADMAP.md §5`.

### One-liner (after steps 1 & 2)

```bash
python -m app.ingest && uvicorn app.main:app --reload --host 0.0.0.0
```

---

## Reaching the backend from Flutter

`localhost` inside an emulator means *the emulator*, not your machine. Use:

| Client | Base URL |
|--------|----------|
| Android emulator | `http://10.0.2.2:8000` |
| iOS simulator | `http://127.0.0.1:8000` |
| Physical device (same Wi-Fi) | `http://<your-LAN-ip>:8000` |
| Flutter web / desktop | `http://127.0.0.1:8000` |

The server must be started with `--host 0.0.0.0` for the first and third rows.
CORS is open to all origins by default for local dev; override it with
`FR_CORS_ORIGINS=http://localhost:3000,https://…` when that matters.

---

## The API contract

The backend commits the contract **before** implementing it, so the frontend is
never blocked on a running server (`ROADMAP.md` §1):

- `docs/api/openapi.yaml` — full spec, generated from the app
- `docs/api/fixtures/*.json` — a real example response per endpoint and state
- `docs/api/README.md` — how they're generated and what each one covers

Regenerate after any change to `backend/app/schemas.py`:

```bash
cd backend && python -m tools.make_contract
```

Renaming or removing a field is a **breaking contract change**: it needs a
`[contract]` PR touching the spec + fixtures, and a reviewer from the other team.
Adding an optional field is safe and needs no ceremony.

---

## Configuration (optional)

All overridable via environment variables — defaults work out of the box:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FR_DATA_DIR` | repo root | folder holding `restaurants.json` / `menu_items.json` |
| `FR_DB_PATH` | `backend/food_roulette.db` | SQLite file location |
| `FR_CORS_ORIGINS` | `*` | comma-separated browser origins allowed to call the API |

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
| `ModuleNotFoundError: pytest` / `httpx` | `pip install -r requirements-dev.txt` |
| `Missing data file: restaurants.json` | run from `backend/`, or set `FR_DATA_DIR` to the folder with the JSON files |
| `/health` shows `restaurants: 0` | you haven't run `python -m app.ingest` yet |
| port 8000 in use | `uvicorn app.main:app --port 8001` |
| App can't reach the API from the emulator | use `10.0.2.2:8000`, and start uvicorn with `--host 0.0.0.0` |
| `test_fixtures.py` fails after a schema change | regenerate: `python -m tools.make_contract` |
