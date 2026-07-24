# Food Roulette — Design Blueprint (Mock-Data Scope)

> Scope locked 2026-07-24. Restaurants around **Thammasat University**, answered
> from the mock `menu_items.xlsx`. This document is the implementation contract;
> `CLAUDE.md` remains the product vision.

## 0. Decisions locked with the owner

| # | Decision | Choice |
|---|----------|--------|
| 1 | Backend | **Flutter client + FastAPI backend** serving mock data (no vector DB) |
| 2 | Chat LLM | **Gemini 2.5 Flash** (non-Claude, cheap, fast, JSON structured output, Thai-capable). Confirm latest model id at build time. |
| 3 | Roulette spin | **Deferred** — becomes a UI *widget later*. Build the core recommendation system first. |
| 4 | Restaurant metadata | Owner will ship a **new `menu_items.xlsx` that includes restaurant names**. **Google Places API** enriches each name → images, reviews, rating, geo, hours. We do **not** fabricate restaurant metadata. |

Guardrail insight from the data: `menu_items.xlsx` has a `confidence` column and
**504 / 1250 dishes are `low`**. For a *hard allergy*, a low-confidence "safe" dish
is unsafe to trust — the deterministic filter treats low-confidence dishes
conservatively (see §4).

---

## 1. Source data (current `menu_items.xlsx`)

1250 rows = **50 restaurants × 25 menu items**.

| Column | Notes |
|--------|-------|
| `restaurant_id` | `tu_place_1` … `tu_place_50` |
| `name_th` | Thai dish name (filled) |
| `name_en` | empty today |
| `category` | **empty today** (no cuisine type) |
| `price_thb` | 10–999, avg ~112 |
| `spicy_level` | 0–3 |
| Allergen flags (0/1) | `crustaceans, fish, milk, eggs, peanuts, tree_nuts, wheat, soy, sesame, molluscs` |
| Dietary flags (0/1) | `contains_meat, contains_pork, contains_beef, contains_alcohol, contains_pungent_veg` |
| `confidence` | `high` / `low` — data-quality of the flags |
| `reviewed_by`, `reviewed_at`, `source_menu_id` | provenance |

**Data now ships as two normalized JSON files** (this replaces the raw xlsx as the
app's source of truth):

- **`restaurants.json`** — dimension table, 50 rows. `id`, `google_place_id` (already
  resolved ✅), `name_th`, `name_en`(null), `latitude`/`longitude` (already resolved ✅,
  clustered around Thammasat Rangsit), `price_band`(null), `is_halal_certified`(0=placeholder),
  `has_parking` (2 = *unknown* sentinel, not "false").
- **`menu_items.json`** — fact table, 1250 rows, joined to restaurants by `restaurant_id`
  (FK integrity verified 50/50). Raw allergen/dietary flags + `confidence`, **plus
  pre-derived diet booleans** `is_vegetarian / is_vegan / is_pescatarian / is_jay`.

Two consequences vs. the earlier plan:
1. `google_place_id` and `lat/lng` are **already present**, so we *skip name→place
   resolution* entirely and do distance ranking offline from day one (§7).
2. Diet suitability is **pre-computed**, so the filter is pure column reads (§4).

Null / sentinel fields (`price_band`, `is_halal_certified`, `has_parking=2`,
`name_en`) mean **"unknown, to be enriched"** — never treat them as `false`. In
particular `is_halal_certified=0` for all 50 means halal must fall back to the
derived pork/alcohol exclusion, not this flag (§4).

---

## 2. System architecture

```
Flutter (Android)                 FastAPI backend                 External
─────────────────                 ───────────────                 ────────
Chat + Profile UI  ──REST/WS──►   /chat  ───────────────►  Gemini 2.5 Flash
Result cards       ◄──JSON────    intent-extraction               (intent → JSON)
History events     ──REST──►      /recommend
                                    │
                                    ├─ deterministic HARD filter  (in-process)
                                    ├─ soft-preference ranking
                                    └─ enrich top-N ──────────►  Google Places API
                                                                 (image, rating, geo)
                                  SQLite: users, prefs,
                                  menu_items, action_history
```

Why FastAPI holds the filter (not the client): the safety-critical exclusion logic
lives server-side so it is **identical for every client** and cannot be bypassed by
a stale app build. The LLM never sees a restaurant until after hard filtering.

---

## 3. Data pipeline & storage

**How the two JSON files are used** — they *are* the normalized DB. Treat
`restaurants.json` as the dimension table and `menu_items.json` as the fact table;
the only join key is `restaurant_id`. Effective usage:

- **Ingest** (`backend/ingest.py`): load both JSON files into SQLite with a real FK
  and indexes: PK on `restaurants.id`, and an index on `menu_items(restaurant_id)`
  plus partial indexes on the flag columns the filter reads most. Because diet flags
  are pre-derived, ingest is a straight copy — no recomputation.
- **Query shape:** the hot path is "for restaurant R, which dishes survive the hard
  filter?" → one indexed lookup per restaurant. Since diet booleans and `confidence`
  are columns, the whole filter is a `WHERE` clause (§4) — no per-request derivation.
- **Idempotent + swappable:** re-running ingest replaces the menu/restaurant tables
  but leaves `users`, `user_preferences`, `action_history` intact, so the owner can
  drop in an updated pair of JSON files without losing history.
- **`google_place_id` is the enrichment key** (not the name) → exact Place Details
  lookups, cached back into the row (§7). `lat/lng` are already local → distance
  works with no API call.

**Storage: SQLite** (file-based, zero-ops, fits mock scope; also persists history).

```sql
CREATE TABLE restaurants (
  id              TEXT PRIMARY KEY,     -- tu_place_N (matches JSON)
  google_place_id TEXT,                 -- already resolved in restaurants.json
  name_th TEXT, name_en TEXT,
  latitude REAL, longitude REAL,
  price_band TEXT,                      -- null today; derivable from menu prices
  is_halal_certified INT,              -- 0=placeholder; do NOT filter on yet
  has_parking INT,                      -- 2 = unknown sentinel
  -- cached Google Places enrichment:
  rating REAL, photo_ref TEXT, hours_json TEXT, places_synced_at TEXT
);

CREATE TABLE menu_items (
  id INTEGER PRIMARY KEY,               -- global id from menu_items.json
  restaurant_id TEXT REFERENCES restaurants(id),
  name_th TEXT, name_en TEXT, category TEXT,
  price_thb REAL, spicy_level INTEGER,
  confidence TEXT,                      -- 'high' | 'low'
  -- raw allergen/dietary flags (0/1)
  crustaceans INT, fish INT, milk INT, eggs INT, peanuts INT, tree_nuts INT,
  wheat INT, soy INT, sesame INT, molluscs INT,
  contains_meat INT, contains_pork INT, contains_beef INT,
  contains_alcohol INT, contains_pungent_veg INT,
  -- pre-derived in menu_items.json:
  is_vegetarian INT, is_vegan INT, is_pescatarian INT, is_jay INT
);
CREATE INDEX idx_menu_rid ON menu_items(restaurant_id);

CREATE TABLE users (id TEXT PRIMARY KEY, display_name TEXT, created_at TEXT);
CREATE TABLE user_preferences (
  user_id TEXT PRIMARY KEY REFERENCES users(id),
  hard_json TEXT,   -- allergens[], religion, intolerances[]
  soft_json TEXT    -- diet style, spicy tolerance, price tier, facilities
);
CREATE TABLE action_history (
  id INTEGER PRIMARY KEY, session_id TEXT, user_id TEXT,
  restaurant_id TEXT, action_type TEXT,  -- IMPRESSION|CLICK|SPIN|REJECTION
  ts TEXT, context TEXT
);
```

---

## 4. The core: deterministic HARD-constraint filter

This is the heart of the app and is **100% code, no LLM**.

**Hard constraints** come from the stored profile *plus* anything the chat explicitly
states ("no pork today"). They map to menu flags:

| Constraint | Rule on a dish | Notes |
|-----------|----------------|-------|
| Allergy: peanuts/shellfish/… | exclude dish if matching flag = 1 | shellfish = `crustaceans OR molluscs` |
| Halal (approx.) | exclude `contains_pork=1 OR contains_alcohol=1` | data has no explicit halal flag; derived |
| No-beef (e.g. Hindu) | exclude `contains_beef=1` | |
| Vegetarian (strict) | require `is_vegetarian=1` | derived flag |
| Jain / no pungent veg | also exclude `contains_pungent_veg=1` | |
| Celiac | exclude `wheat=1` | |

**Confidence handling — tiered, never empty-handed (revised per owner):**
Low confidence no longer means "hide the dish." Instead every dish that *passes* the
hard flag filter is labelled into one of two tiers, and the app degrades gracefully:

| Tier | Condition | UI behaviour |
|------|-----------|--------------|
| **A — Verified safe** | passes filter **and** `confidence='high'` | shown normally |
| **B — Likely safe, unverified** | passes filter but `confidence='low'` | shown with a caution badge; requires user acknowledgement before it counts |

Acknowledgement policy scales with severity of the constraint that made the dish
risky:
- **Hard allergy (medical):** a Tier-B dish shows a ⚠ "allergen data unverified"
  badge and needs an **explicit per-session confirm** ("I understand this dish's
  allergen info isn't verified") before it can be picked / land in the roulette.
- **Religion / diet style:** a passive badge is enough, no blocking dialog.

**Fallback rule:** results prefer Tier A. If the hard filter yields **zero Tier-A**
dishes for a restaurant (or across all restaurants), we **do not return nothing** —
we surface Tier B behind a banner: *"No verified-safe options found; here are likely-safe
ones you'll need to confirm."* This guarantees the app always has something to show
while keeping the user in control of the risk. The response marks each dish/restaurant
with `safety_tier: "verified" | "unverified"` and a `needs_ack` boolean so the client
renders the right badge and gate.

**Restaurant viability:** a restaurant is recommendable iff it has ≥1 dish that
survives the hard filter (Tier A or B). Cards carry the restaurant's best tier so the
list can sort verified-safe places first. (Validated: 47/50 restaurants have a
vegetarian dish; every restaurant has peanut-safe *high-confidence* dishes, so Tier A
is usually non-empty — Tier B is the graceful floor, not the norm.)

Output of this stage: `List<(restaurant, safe_dishes[])>` — the *only* thing the
ranking and LLM stages are ever allowed to see.

---

## 5. Soft-preference ranking

Applied to the already-safe set (never excludes on safety):
- spicy tolerance vs `spicy_level`
- price tier vs `price_thb`
- diet style (keto/low-carb bias) as a soft score
- distance from `latitude/longitude` (already local — no API call) and rating
- history penalty: down-rank restaurants rejected earlier in the session

Returns top-N restaurants with a score; ties broken randomly (seed of the later
roulette widget).

---

## 6. AI chat layer + guardrail strategy (Gemini 2.5 Flash)

Two-call sandwich, with deterministic filtering in the middle so the LLM can never
cause an allergy error or hallucinate a restaurant:

```
1. EXTRACT  Gemini(structured output) :  user text → {
              cravings, detected_hard_constraints, soft_prefs, facility_needs }
2. FILTER   deterministic §4 + §5      :  → top-N safe restaurants  (NO LLM)
3. NARRATE  Gemini(temperature low)    :  given ONLY the filtered list,
              write the friendly reply. Grounded — cannot invent venues.
```

- Step 1 uses Gemini **JSON schema / structured output** so we parse, not free-text.
- Step 3 is given the concrete restaurant+dish JSON and instructed to reference only
  those ids; the app renders cards from the structured data, not the prose.
- If extraction surfaces a *new* hard constraint, it is unioned with the stored
  profile before filtering — the safe direction.

---

## 7. Google Places enrichment

- Keyed by the **`google_place_id` already in `restaurants.json`** → a direct Place
  Details call, no ambiguous name search, no geocoding step.
- Lazy + cached: on first recommendation of a restaurant, fetch photo reference,
  rating, reviews, opening hours → cache into the `restaurants` row + `places_synced_at`.
  `latitude/longitude` are already local, so distance never waits on Places.
- App shows Places rating/photo/reviews; **safety flags always come from our mock
  data, never from Places.**
- `price_band` (null today) can be derived offline from each restaurant's menu price
  distribution as a stopgap until a real value exists.
- Backend holds the Places key; the client never sees it.

---

## 8. API design (Flutter ↔ FastAPI)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/session` | mock login → user_id + token (real OAuth deferred) |
| GET/PUT | `/users/{id}/preferences` | read/update hard + soft profile |
| POST | `/chat` | `{session_id, text}` → `{reply, recommendations[]}` (steps §6) |
| POST | `/recommend` | filter-only path (no chat) → `recommendations[]` |
| GET | `/restaurants/{id}` | full detail incl. Places enrichment + safe dishes |
| POST | `/history` | log `IMPRESSION\|CLICK\|SPIN\|REJECTION` |

`recommendation` object → `{restaurant_id, name, rating, photo_url, distance_m,
price_tier, safe_dishes:[{name_th, price_thb, spicy_level}], excluded_count}`.

WebSocket variant of `/chat` is optional for streaming the narration later.

---

## 9. Flutter app

**State management: Riverpod** (recommended). The chat feed is a stream of typed
messages where some messages *are* recommendation-card widgets; Riverpod's
`AsyncNotifier` + families model "profile", "chat session", and "history" cleanly
without Bloc boilerplate, and rebuilds only the cards that change.

Screens: **Onboarding/Profile** (hard + soft prefs) → **Chat** (feed with embedded
restaurant cards) → **Restaurant detail** (Places photos/reviews + safe-dish list)
→ **History**.

---

## 10. Build phases

- **Phase 1 — Core (now):** ingest `restaurants.json` + `menu_items.json` → SQLite;
  deterministic hard filter with the tiered confidence model (§4) + soft ranking;
  `/recommend` + `/preferences`; minimal Flutter profile + results list.
  *Proves the safety engine end-to-end with no LLM and no Places.*
- **Phase 2 — Chat:** Gemini extract/narrate sandwich; `/chat`; chat UI.
- **Phase 3 — Places:** enrichment + restaurant detail screen.
- **Phase 4 — History & feedback loop:** logging + session-level rejection penalty.
- **Phase 5 — Roulette widget:** spin animation over the already-filtered set.

---

## 11. Decisions — all confirmed by owner (2026-07-24)

1. ✅ **SQLite** as the backend store (persists history across data re-ingests).
2. ✅ **Mock auth** in Phase 1; real Firebase/OAuth deferred.
3. ✅ **Gemini 2.5 Flash** for chat (Flash-Lite for the pure extraction step to cut
   cost). Verify the latest model id at build time.
4. ✅ Repo layout: `backend/` (Python/FastAPI) alongside the Flutter root.
5. ✅ **Confidence handling:** tiered verified/unverified with acknowledgement + Tier-B
   fallback (§4) instead of hard exclusion — so the app is never empty-handed.
