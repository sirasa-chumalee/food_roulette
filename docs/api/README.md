# API contract

The promise the backend makes to the Flutter client. See `ROADMAP.md` §1 and §3
for the rules around it; this file explains what's here and where it came from.

```
docs/api/
├── openapi.yaml     # generated from the running FastAPI app
├── fixtures/        # one real example response per endpoint/state
└── README.md
```

## Regenerating

Both the spec and the fixtures are generated — **never hand-edit them**:

```bash
cd backend
python -m tools.make_contract
```

The spec is dumped from the live app, and the fixtures are captured from real
requests against a throwaway database built from `restaurants.json` /
`menu_items.json`. To change the contract, change the pydantic models in
`backend/app/schemas.py` and re-run the generator.

`backend/tests/test_fixtures.py` validates every committed fixture against those
models, so a schema change without a regeneration fails the suite rather than
silently breaking the frontend's mocks.

## Fixtures and their provenance

| File | Endpoint | How it was produced |
|------|----------|---------------------|
| `health.json` | `GET /health` | real response |
| `register.json` | `POST /auth/register` | real response (the fixture user the generator registers) |
| `preferences.json` | `PUT /preferences` (bearer token) | real response |
| `recommend_all_verified.json` | `POST /recommend` | real — peanut + shellfish allergy, halal; the one Tier-B venue of the 50 is selected out |
| `recommend_mixed.json` | `POST /recommend` | real — Jain profile, cards selected to show both tiers |
| `recommend_unverified_only.json` | `POST /recommend` | **synthesised** (see below); the cards inside are real |
| `recommend_empty.json` | `POST /recommend` | **synthesised** (see below) |
| `chat_with_cards.json` | `POST /chat` | real — "อยากกินอะไรเผ็ดๆ ไม่เอาหมู", canned Gemini answers (see below) |
| `chat_no_cards.json` | `POST /chat` | **synthesised** — same reason as `recommend_empty.json`; the reply is the server's real constant |
| `chat_degraded.json` | `POST /chat` | real — the Gemini-outage path, byte-for-byte what a keyless deployment returns |
| `restaurant_detail.json` | `GET /restaurants/{id}` | real — keyless (nulls) response; the degraded "works, just plainer" state |
| `restaurant_detail_enriched.json` | `GET /restaurants/{id}` | real endpoint response with a **seeded** cache (no real Places call); shows rating/photos/reviews/hours |
| `error_not_found.json` | any | real 404 — valid token, unknown account |
| `error_invalid_prefs.json` | any | real 422 |

Responses are truncated to 3 cards × 3 dishes for readability. **Restaurant detail fixtures are NOT truncated** — the fixture shows the full 25-dish menu so the detail screen can be built from a realistic payload.

### Why two fixtures are synthesised

Every constraint set was swept against all 50 restaurants / 1250 dishes. Over the
current dataset:

- **no profile produces an all-unverified response** — 746 of 1250 dishes are
  `confidence='high'` and they're spread across every restaurant, so Tier A is
  almost always non-empty. The strongest real case (Jain) leaves exactly **one**
  restaurant unverified, which is what `recommend_mixed.json` captures.
- **no profile produces an empty response** — even vegan + celiac + Jain + all
  nine allergens still leaves 44 restaurants with a safe dish.

Both states are nonetheless reachable in production (a stricter dataset, a
distance radius, a smaller catchment), and `ROADMAP` M1 requires the frontend to
render all four, so the fixtures exist. This matches `docs/DESIGN.md` §4: Tier B
is the graceful floor, not the norm.

### Why the chat fixtures use canned Gemini answers

`chat_with_cards.json` is a real `POST /chat` response — same extraction union,
same filter, same ranking, same card shapes — but the two Gemini calls are
stubbed by the generator. A live model would make the file change on every
regeneration, and would require a key to build the contract at all. The stubbed
extraction (`no_pork` + spicy) is exactly what the message means, and the reply is
written from the cards the filter actually returned, so it passes the same
grounding check the server applies at runtime.

`chat_degraded.json` needs no stub reasoning: it's what every request returns when
`GEMINI_API_KEY` is unset.

## Notes for the frontend

- `rating` and `photo_url` on the **recommendation card** (`POST /recommend`, `POST /chat`) are
  still `null` in the current response shape. The `GET /restaurants/{id}` detail
  endpoint now returns Places enrichment (rating, photos, reviews, opening hours)
  when a `GOOGLE_PLACES_API_KEY` is configured, and degrades to nulls otherwise.
  See `restaurant_detail.json` and `restaurant_detail_enriched.json` for both states.
- `price_tier` is now populated (`$`…`$$$$`, derived at ingest from each menu's
  median price). It can still be `null` for a venue with no priced dish — show
  "unknown", not "cheap".
- `distance_m` is present whenever the request carried `latitude`/`longitude`.
- `needs_ack: true` always comes with a non-null `ack_reason` — show it verbatim
  in the confirmation dialog.
- `POST /recommend` takes an optional `seed`. Same seed + same profile ⇒ same
  order, which is what makes an M5 roulette spin replayable. Omit it and ties
  reshuffle on every call.
- `hard.jay` (Thai เจ: vegan + no pungent vegetables) sits alongside `hard.jain`
  (vegetarian + no pungent vegetables). They are different constraints.
- `POST /chat` returns the **same** `recommendation` objects as `/recommend`, plus
  `reply`, `session_id`, `fallback_used` and `degraded`. Render cards from
  `recommendations` — never by parsing `reply`. That separation is the guardrail
  (DESIGN §6), and the backend enforces its half of it: a reply naming a
  restaurant that isn't in the response is thrown away before it's sent.
- **A Gemini outage is not an error response.** `/chat` still returns `200` with
  real cards and `degraded: "LLM_UNAVAILABLE" | "UPSTREAM_TIMEOUT"`; only the
  prose is canned. Show the inline notice, keep the results
  (`chat_degraded.json`). `/chat` only 4xx-s for a bad request or unknown user.
- `session_id`: omit it on the first message, then send back what you were given.
  It groups a conversation and is what M3's history events will hang off.
- Heads-up on the data, not the API: a few source rows still contradict their own
  names. `bb254df` fixed 19 of them (the fixtures were regenerated on top of it), but
  `ต้มแซ่บกระดูกอ่อน` is still `is_vegan: true` / `is_jay: true` at
  `confidence: "high"`, so a vegan profile can surface it with a *verified* badge.
  The filter is behaving correctly; the input is wrong. Don't file it as a filter
  bug — it's tracked as a data risk in `ROADMAP` §6.
- Errors always arrive as `{"error": {code, message, detail}}`. `message` is safe
  to display; `detail` is for logs only.
- Error codes: `NO_RESULTS`, `INVALID_PREFS`, `NOT_FOUND`, `LLM_UNAVAILABLE`,
  `UPSTREAM_TIMEOUT`, `INTERNAL`. (`NOT_FOUND` was added to the `ROADMAP` §3.2
  list during M0 — a 404 needed a code of its own.)
