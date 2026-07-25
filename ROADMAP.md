# Food Roulette — Delivery Roadmap (Frontend ↔ Backend)

> **Audience:** the Flutter team and the FastAPI team, working in parallel in one repo.
> **Authority:** `CLAUDE.md` = product vision · `docs/DESIGN.md` = technical contract ·
> **this file = who builds what, in what order, and where the two tracks meet.**
> If this file and `docs/DESIGN.md` disagree, DESIGN.md wins on *how*, this file wins on *when/who*.

Last updated 2026-07-25.

---

## 0. Ground truth — where we actually are today

Verified against the repo, not assumed:

| Area | State | Evidence |
|------|-------|----------|
| Data | ✅ Ready | `restaurants.json` (50 rows), `menu_items.json` (1250 rows) at repo root |
| DB schema | ✅ Written | `backend/schema.sql` — restaurants, menu_items, users, user_preferences, action_history |
| Ingest | ✅ Written | `backend/app/ingest.py` (idempotent; rebuilds reference tables only) |
| Backend API | 🟡 Scaffold only | `backend/app/main.py` = `/health`, `/restaurants`, `/restaurants/{id}` (smoke tests) |
| Local DB file | ❌ Not built | `backend/food_roulette.db` absent — every dev runs `python -m app.ingest` once |
| Hard filter / ranking | ❌ Not started | The core safety engine (DESIGN §4–§5) |
| Auth, preferences, chat, Places, history | ❌ Not started | — |
| Flutter app | ❌ Stock template | `lib/main.dart` is the counter demo; no Riverpod, no HTTP client, no models |
| Flutter deps | ❌ Minimal | `pubspec.yaml` has only `cupertino_icons` + `flutter_lints` |

**Implication:** the frontend is ~one milestone behind the backend. M1 must let FE catch up on
scaffolding *while* BE builds the filter — which only works if the API contract is frozen first.

---

## 1. How the two teams stay unblocked (read this before anything else)

The default failure mode for a split team is: **FE waits for a running backend, BE waits for FE to
say what it needs.** We avoid it with three rules.

### Rule 1 — Contract before code
At the start of every milestone, backend commits the contract **before** implementing it:

```
docs/api/openapi.yaml        # request/response schemas for that milestone's endpoints
docs/api/fixtures/*.json     # a real, valid example response per endpoint
```

Frontend builds against the fixtures. A fixture is a *promise*: if BE later changes it, that's a
contract change (Rule 3), not a bugfix.

### Rule 2 — Frontend never waits for a live server
FE's API client sits behind one interface with two implementations, chosen by a build flag:

```dart
abstract class FoodRouletteApi { ... }
class MockApi  implements FoodRouletteApi  // reads docs/api/fixtures/*.json from assets
class HttpApi  implements FoodRouletteApi  // real dio/http client
```

`flutter run --dart-define=USE_MOCK=true` is the default until each milestone's integration day.
This also gives us deterministic widget tests forever.

### Rule 3 — Contract changes are announced, never silent
Changing a field name/shape after the fixture is committed requires: a PR touching
`openapi.yaml` + fixtures + a note in the PR title `[contract]`. Additive fields (new optional key)
are safe and don't need ceremony. Breaking changes get an integration checkpoint.

### Rule 4 — Safety logic lives **only** in the backend
The frontend must **never** re-implement or second-guess allergen/religious filtering. It renders
what it's told. If a card arrives, it's already been through the deterministic filter
(DESIGN §4). FE's only safety job is honouring `safety_tier` and `needs_ack` (see §3).
This is non-negotiable — a stale app build must not be able to bypass a medical constraint.

---

## 2. Ownership map

| Layer | Owner | Files |
|-------|-------|-------|
| Data ingest, SQLite | Backend | `backend/app/ingest.py`, `backend/schema.sql` |
| Hard filter + ranking | Backend | `backend/app/filter.py`, `ranking.py` (new) |
| REST endpoints | Backend | `backend/app/main.py`, `routers/` |
| Gemini extract/narrate | Backend | `backend/app/llm/` (new) |
| Google Places enrichment | Backend | `backend/app/places.py` (new) |
| **API contract + fixtures** | **Backend authors, both review** | `docs/api/` |
| API client, models | Frontend | `lib/data/` |
| State (Riverpod) | Frontend | `lib/state/` |
| Screens, widgets | Frontend | `lib/features/` |
| Safety badge / ack UX | **Both** — BE defines flags, FE defines interaction | — |

**Secrets:** Gemini and Google Places keys live in `backend/.env` (git-ignored) and are read via
`config.py`. The Flutter client never holds an API key. Keys are requested from the owner at M3/M4,
not committed, not pasted in chat.

---

## 3. The two cross-team contracts that matter most

Everything else is plumbing. Get these two right and the milestones fall into place.

### 3.1 The `recommendation` object
This is the single object the whole UI is built from. Frozen at **M1**, extended (additively) later.

```jsonc
{
  "restaurant_id": "tu_place_12",
  "name_th": "...",
  "name_en": null,                 // null = unknown, render name_th
  "latitude": 14.07, "longitude": 100.60,
  "distance_m": 480,               // computed offline, always present
  "price_tier": "$$",              // derived from menu prices; null until derived
  "rating": null,                  // M4 (Places). null until then — FE hides the stars
  "photo_url": null,               // M4. null until then — FE shows a placeholder
  "safety_tier": "verified",       // "verified" | "unverified"  ← DESIGN §4
  "needs_ack": false,              // true ⇒ FE must gate selection behind a confirm
  "ack_reason": null,              // e.g. "allergen data unverified for: peanuts"
  "safe_dishes": [
    { "id": 412, "name_th": "...", "price_thb": 60, "spicy_level": 1,
      "safety_tier": "verified" }
  ],
  "excluded_count": 18             // dishes removed by the hard filter — powers the "we filtered N" line
}
```

**FE rendering rules (binding):**
- `safety_tier: "unverified"` → caution badge on the card **and** on the affected dish.
- `needs_ack: true` → the user cannot select / spin / open-for-order that card until they confirm
  an explicit dialog. Acknowledgement is **per session**, per restaurant.
- A response may legitimately contain *only* unverified results — render the fallback banner
  ("No verified-safe options found…"), never an empty state.
- Never suppress a card because FE thinks it looks unsafe. Report a suspected filter bug instead.

### 3.2 Error envelope
Every non-2xx from the backend, no exceptions:

```jsonc
{ "error": { "code": "NO_RESULTS" | "INVALID_PREFS" | "LLM_UNAVAILABLE" | "UPSTREAM_TIMEOUT" | "INTERNAL",
             "message": "human-readable, safe to show the user",
             "detail": null } }
```

FE maps `code` → UI treatment. `message` is displayable; `detail` is for logs only. BE never leaks
a stack trace into `message`.

---

## 4. Milestones

Five milestones, mirroring `docs/DESIGN.md` §10. Durations are *effort estimates for a small team* —
the owner sets calendar dates. Each milestone ends in a **joint integration checkpoint**: FE flips
`USE_MOCK=false` and both teams sit together until the real flow works on a device.

---

### M0 — Foundations (≈2 days) · both tracks, mostly parallel

Goal: every developer can run both halves, and FE has somewhere to put code.

**Backend**
- [ ] `README` section: create venv → `pip install -r requirements.txt` → `python -m app.ingest` → `uvicorn app.main:app --reload`
- [ ] Verify ingest on a clean clone; `/health` reports `restaurants: 50, menu_items: 1250`
- [ ] Enable CORS for local Flutter dev + bind `--host 0.0.0.0` (Android emulator reaches the host at `10.0.2.2`)
- [ ] `pytest` set up with a throwaway DB (`--db` flag already exists in ingest)
- [ ] Commit `docs/api/openapi.yaml` skeleton + the M1 fixtures

**Frontend**
- [ ] Replace the counter template in `lib/main.dart`
- [ ] Add deps: `flutter_riverpod`, `dio` (or `http`), `freezed` + `json_serializable`, `go_router`, `geolocator`
- [ ] Folder skeleton:
  ```
  lib/
    core/          # theme, constants, env (API base url via --dart-define)
    data/
      models/      # freezed models generated from the contract
      api/         # FoodRouletteApi + MockApi + HttpApi
    state/         # Riverpod providers / AsyncNotifiers
    features/
      profile/ results/ chat/ detail/ history/
  ```
- [ ] `MockApi` reads `docs/api/fixtures/` (wired in as a Flutter asset dir)
- [ ] App boots to an empty shell with routing between the 5 feature screens

**Checkpoint:** BE serves `/health`; FE app runs on an emulator and renders a stub screen from a fixture.
**DoD:** a new teammate can clone the repo and get both halves running from the README alone.

---

### M1 — The safety engine (≈1 week) · **the most important milestone**

Goal: prove the deterministic hard filter end-to-end with **no LLM and no Places**. If this is
wrong, nothing built on top of it is safe.

**Backend**
- [ ] `filter.py` — hard-constraint filter as a pure `WHERE` clause (DESIGN §4):
      allergens (shellfish = `crustaceans OR molluscs`), halal → exclude `contains_pork OR contains_alcohol`
      (**not** `is_halal_certified`, which is a placeholder `0` for all 50 rows), no-beef, vegetarian/vegan/jay,
      pungent-veg, celiac → `wheat`
- [ ] Tiering: passing dishes labelled `verified` (`confidence='high'`) / `unverified` (`confidence='low'`);
      Tier-B fallback so a response is **never empty** when any dish survives
- [ ] `ranking.py` — soft scoring: spicy tolerance, price tier, diet style, haversine distance
      (lat/lng are already local — no API call), random tiebreak
- [ ] Derive `price_tier` per restaurant from its menu price distribution (fills the null `price_band`)
- [ ] Endpoints: `POST /auth/session` (mock), `GET|PUT /users/{id}/preferences`, `POST /recommend`
- [ ] **Test suite is the deliverable here**, not the endpoint:
      - a peanut allergy returns zero dishes with `peanuts=1` — assert across all 1250 rows
      - halal returns zero pork/alcohol dishes
      - a constraint with no Tier-A matches still returns Tier-B + the fallback flag
      - property test: for every generated constraint set, no returned dish violates it

**Frontend**
- [ ] Preferences/onboarding screen: hard constraints (allergen multi-select, religion, intolerances)
      + soft prefs (diet style, spicy, price tier, facilities) → `PUT /preferences`
- [ ] Results list rendering `recommendation[]` from fixtures
- [ ] Restaurant card widget incl. **safety badge**, Tier-B caution styling, and the acknowledgement dialog
- [ ] Fallback banner state + "we filtered out N dishes" affordance
- [ ] Riverpod: `profileProvider`, `recommendationsProvider` (AsyncNotifier)

**Contract handoff:** BE commits `fixtures/recommend.json` covering **four** cases —
all-verified, mixed, unverified-only (fallback), and genuinely-empty. FE builds all four states.

**Checkpoint:** FE switches to `HttpApi`; set a real allergy in the UI and confirm on-device that no
offending dish appears.
**DoD:** a peanut-allergic profile produces recommendations with zero peanut dishes, proven by
backend tests *and* observed on a device.

---

### M2 — Chat (≈1 week)

Goal: the Gemini extract → filter → narrate sandwich (DESIGN §6). The LLM never sees a restaurant
until after the M1 filter has run.

**Backend**
- [ ] `llm/extract.py` — Gemini structured output: text → `{cravings, hard_constraints, soft_prefs, facility_needs}`
      (use the cheaper Flash-Lite tier for this step; confirm the current model id at build time)
- [ ] Union any chat-detected hard constraint with the stored profile — **union, never override**
- [ ] `llm/narrate.py` — low temperature, given *only* the filtered list, instructed to reference
      returned ids only. Prose is decoration; cards render from structured data.
- [ ] `POST /chat` → `{reply, recommendations[], session_id}`
- [ ] Graceful degradation: if Gemini is down → `LLM_UNAVAILABLE`, but still return `/recommend`
      results from the stored profile. Chat failure must not break the core product.
- [ ] Guardrail test: assert every restaurant id mentioned in `reply` exists in `recommendations[]`

**Frontend**
- [ ] Chat feed: typed message stream where some messages **are** recommendation-card widgets
- [ ] Composer, pending/typing state, per-message error state
- [ ] `chatSessionProvider` (AsyncNotifier) holding the message list + session id
- [ ] Handle `LLM_UNAVAILABLE` by falling back to the plain results view with an inline notice

**Contract handoff:** `fixtures/chat.json` — a reply with cards, a reply with no cards, an error case.
**DoD:** typing "อยากกินอะไรเผ็ดๆ ไม่เอาหมู" (spicy, no pork) returns a grounded reply and cards
containing no pork dishes.

---

### M3 — History & feedback loop (≈3 days)

Deliberately placed **before** Places: it's cheap, needs no API key, and immediately improves results.

**Backend**
- [ ] `POST /history` logging `IMPRESSION | CLICK | SPIN | REJECTION` with session id + conversational context
- [ ] Accept **batched** events (FE buffers impressions; one request per N events or per few seconds)
- [ ] Session-scoped rejection penalty feeding `ranking.py` — a rejected restaurant is down-ranked
      for the rest of the session
- [ ] `GET /history?user_id=` for the History screen

**Frontend**
- [ ] Fire-and-forget event buffer (never blocks or fails a UI interaction)
- [ ] Impression tracking on card visibility; click on detail open; rejection on dismiss
- [ ] History screen

**DoD:** rejecting a card in-session measurably demotes it on the next recommendation call.

---

### M4 — Google Places enrichment (≈4 days) · *gated on the owner supplying an API key*

**Backend**
- [ ] `places.py` — Place Details keyed by the `google_place_id` already in `restaurants.json`
      (no name search, no geocoding)
- [ ] Lazy + cached into the restaurant row + `places_synced_at`; a stale/failed lookup degrades to nulls
- [ ] Photo proxied or signed **through the backend** — the client never sees the key
- [ ] `GET /restaurants/{id}` extended: Places rating/photos/reviews/hours + safe-dish list
- [ ] **Safety flags always come from our data, never from Places**

**Frontend**
- [ ] Restaurant detail screen: photos, rating, reviews, opening hours, safe-dish list
- [ ] Every Places-sourced field renders gracefully when null (M1–M3 already exercised this path)

**DoD:** detail screen shows real photos/ratings; with the key removed the app still works, just plainer.

---

### M5 — Roulette widget (≈3 days)

The product's namesake, last by design (DESIGN §3, decision 3) — it spins over the *already filtered*
set, so it inherits M1's guarantees for free.

- **Backend:** expose the ranked candidate set + a seed so a spin is reproducible; log `SPIN`
- **Frontend:** spin animation, result reveal, re-spin; **a Tier-B result must clear its acknowledgement
  gate before it can win a spin**

**DoD:** spinning never lands on a dish violating a hard constraint, and never silently lands on an
unacknowledged Tier-B result.

---

## 5. Working agreements

- **Branches:** `feat/be-<topic>`, `feat/fe-<topic>`. Contract changes: `contract/<topic>`.
- **PRs:** small, one milestone item each. Cross-team-visible changes need a reviewer from the other team.
- **`main` stays runnable.** Both halves must boot on `main` at all times.
- **Backend tests gate merges** for anything touching `filter.py` / `ranking.py`. No exceptions —
  this is the medical-safety path.
- **Integration checkpoints are scheduled, not improvised.** One per milestone, both teams present.
- **Blocked?** Post the blocker with the fixture you need. Never invent a response shape and hope —
  that's how the two halves silently diverge.
- **Android emulator reaches the host backend at `10.0.2.2:8000`**, not `localhost`. Put it in the
  README; it costs every new dev an hour otherwise.

## 6. Risks & open items

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| `confidence='low'` on 504/1250 dishes | A "safe" dish may be mislabelled — a medical risk | Tier A/B model + explicit acknowledgement (DESIGN §4). Never silently trust Tier B. | Backend |
| `is_halal_certified` is a placeholder `0` for all 50 | Filtering on it excludes everything | Derive halal from pork/alcohol; do **not** read that column | Backend |
| `has_parking = 2` means *unknown*, not false | Wrongly excludes venues | Sentinel-aware filters; UI says "unknown", not "no parking" | Both |
| `category` and `name_en` empty | Weak cuisine-type semantics; Thai-only labels | Cravings match on dish names for now; category enrichment is post-M5 | Backend |
| Gemini model id drift | Runtime failures | Confirm the current Flash model id at build time; pin it in `config.py` | Backend |
| Places key not yet supplied | M4 blocks | M4 is sequenced late and every Places field is nullable end-to-end | Owner |
| Real auth deferred (mock session) | Not shippable to real users | Firebase/OAuth swap-in scoped after M5; keep auth behind one interface | Backend |

**Open questions for the owner**
1. Is the updated `menu_items.xlsx` with restaurant names still coming, or are the current JSON files final?
2. Google Places billing account / API key — when?
3. Target device & Android minSdk for testing?
4. Thai-only UI, or Thai + English from the start? (Affects M1 screens, not just copy.)
