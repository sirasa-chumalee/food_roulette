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
| `auth_session.json` | `POST /auth/session` | real response |
| `preferences.json` | `PUT /users/{id}/preferences` | real response |
| `recommend_all_verified.json` | `POST /recommend` | real — peanut + shellfish allergy, halal |
| `recommend_mixed.json` | `POST /recommend` | real — Jain profile, cards selected to show both tiers |
| `recommend_unverified_only.json` | `POST /recommend` | **synthesised** (see below); the cards inside are real |
| `recommend_empty.json` | `POST /recommend` | **synthesised** (see below) |
| `error_not_found.json` | any | real 404 |
| `error_invalid_prefs.json` | any | real 422 |

Responses are truncated to 3 cards × 3 dishes for readability. Nothing else about
them is edited — field names, nulls and value types are exactly what the server
sends.

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

## Notes for the frontend

- `rating` and `photo_url` are `null` until M4 (Google Places). Render a
  placeholder — don't hide the card.
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
- Errors always arrive as `{"error": {code, message, detail}}`. `message` is safe
  to display; `detail` is for logs only.
- Error codes: `NO_RESULTS`, `INVALID_PREFS`, `NOT_FOUND`, `LLM_UNAVAILABLE`,
  `UPSTREAM_TIMEOUT`, `INTERNAL`. (`NOT_FOUND` was added to the `ROADMAP` §3.2
  list during M0 — a 404 needed a code of its own.)
