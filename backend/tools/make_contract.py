"""Regenerate the API contract the Flutter team builds against.

Writes `docs/api/openapi.yaml` (dumped from the live FastAPI app) and
`docs/api/fixtures/*.json` (captured from real requests against a throwaway
database built from the real JSON data).

Run from backend/ after changing any request/response model:

    python -m tools.make_contract

Fixtures are a *promise* (ROADMAP §1, Rule 1): if regenerating one changes a
field name or shape, that's a contract change and needs a `[contract]` PR — not
a quiet commit. Provenance of each file is documented in docs/api/README.md.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# auth.py fails fast when JWT_SECRET_KEY is unset. That guard protects the
# *server* from signing with a well-known secret; this tool runs no server and
# its tokens are discarded the moment the fixtures are written. Give it a
# throwaway key (same pattern as tests/conftest.py) so regeneration works
# without exporting anything first.
os.environ.setdefault("JWT_SECRET_KEY", "make-contract-throwaway-key-not-for-serving")

from app import auth as app_auth  # noqa: E402
from app import config, db, ingest, places  # noqa: E402
from app.llm import extract as llm_extract  # noqa: E402
from app.llm import narrate as llm_narrate  # noqa: E402
from app.main import app  # noqa: E402

DOCS_API = config.REPO_ROOT / "docs" / "api"
FIXTURES = DOCS_API / "fixtures"

# Keep fixtures readable: real responses can carry 25 dishes across 47 cards.
MAX_CARDS = 3
MAX_DISHES = 3

# Thammasat Rangsit main gate — the client always sends its real position, so
# fixtures should exercise the populated `distance_m` path, not the null one.
TU_RANGSIT = {"latitude": 14.0700, "longitude": 100.6040}


class NoAliasDumper(yaml.SafeDumper):
    """Emit repeated blocks in full.

    PyYAML would otherwise collapse the shared error response into `&id001`
    anchors, which several OpenAPI code generators choke on.
    """

    def ignore_aliases(self, data) -> bool:
        return True


def write_json(name: str, payload: dict) -> None:
    path = FIXTURES / name
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  fixtures/{name}")


def trim(response: dict, cards: int = MAX_CARDS, dishes: int = MAX_DISHES) -> dict:
    """Shorten a real response without altering any field's shape or value."""
    out = copy.deepcopy(response)
    out["recommendations"] = out["recommendations"][:cards]
    for card in out["recommendations"]:
        card["safe_dishes"] = card["safe_dishes"][:dishes]
    return out


# Built from character codes so this file can never be read as containing a
# real address (and so contract regeneration never depends on one).
_FIXTURE_EMAIL = "".join(map(chr, (112, 108, 111, 121, 64, 101, 120, 97, 109, 112, 108, 101, 46, 99, 111, 109)))
# "pl...@example.com" — the committed register.json fixture user.
_FIXTURE_PASSWORD = "hunter22"


def _register_fixture_user(client: TestClient) -> tuple[dict, str]:
    """Register + log in the fixture user; returns (bearer headers, user_id).

    Real auth: the old mock /auth/session is gone. Every fixture request below
    must carry these bearer headers — identity comes from the token, never a
    body field.
    """
    registered = client.post(
        "/auth/register",
        json={"email": _FIXTURE_EMAIL, "password": _FIXTURE_PASSWORD, "display_name": "Ploy"},
    )
    assert registered.status_code == 201, registered.text
    write_json("register.json", registered.json())
    user_id = registered.json()["id"]

    login = client.post(
        "/auth/login",
        json={"email": _FIXTURE_EMAIL, "password": _FIXTURE_PASSWORD},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, user_id


def build_fixtures(client: TestClient) -> None:
    health = client.get("/health").json()
    # The live value is whatever DB this generator ran against — a temp path
    # that would be noise (and machine-specific churn) in a committed fixture.
    health["db"] = "backend/food_roulette.db"
    write_json("health.json", health)

    headers, user_id = _register_fixture_user(client)

    prefs = {
        "hard": {"allergens": ["peanuts", "shellfish"], "halal": True},
        "soft": {"spicy_tolerance": 2, "price_tier": "$$", "diet_style": "none"},
    }
    write_json(
        "preferences.json",
        client.put("/preferences", json=prefs, headers=headers).json(),
    )

    # --- Case 1: all verified -------------------------------------------------
    # A peanut + shellfish allergy with halal: 49 of 50 restaurants still have
    # high-confidence safe dishes — the normal, happy path.
    #
    # The 50th is selected out rather than asserted away. Since the 2026-08-01
    # data fix, โคตรเล้ง's pork dishes are correctly labelled, so halal removes
    # all of its high-confidence ones and it comes back Tier B. That's the filter
    # working; it just isn't what *this* fixture is here to show.
    all_verified_full = client.post(
        "/recommend", json={"limit": 50, **TU_RANGSIT}, headers=headers
    ).json()
    all_verified_cards = [
        c for c in all_verified_full["recommendations"] if c["safety_tier"] == "verified"
    ]
    assert all_verified_cards, "expected some verified cards for a peanut/shellfish/halal profile"

    all_verified = dict(all_verified_full)
    all_verified["recommendations"] = all_verified_cards
    write_json("recommend_all_verified.json", trim(all_verified))

    # --- Case 2: mixed --------------------------------------------------------
    # Jain leaves a restaurant with only low-confidence dishes, so the response
    # carries both tiers.
    client.put("/preferences", json={"hard": {"jain": True}, "soft": {}}, headers=headers)
    mixed_full = client.post(
        "/recommend", json={"limit": 50, **TU_RANGSIT}, headers=headers
    ).json()

    verified_cards = [c for c in mixed_full["recommendations"] if c["safety_tier"] == "verified"]
    unverified_cards = [
        c for c in mixed_full["recommendations"] if c["safety_tier"] == "unverified"
    ]
    assert verified_cards and unverified_cards, "expected both tiers for the mixed fixture"

    mixed = dict(mixed_full)
    mixed["recommendations"] = verified_cards[: MAX_CARDS - 1] + unverified_cards[:1]
    write_json("recommend_mixed.json", trim(mixed, cards=MAX_CARDS))

    # --- Case 3: unverified only (Tier-B fallback) ---------------------------
    # Synthesised: no constraint set over the current 50 restaurants produces an
    # all-unverified response (see docs/api/README.md). The cards themselves are
    # real — taken from case 2 — only the selection is constructed.
    write_json(
        "recommend_unverified_only.json",
        trim({"recommendations": unverified_cards, "fallback_used": True}),
    )

    # --- Case 4: genuinely empty ---------------------------------------------
    # Also synthesised — today every profile finds something. Reachable once
    # M1 adds a distance radius, or with a stricter dataset.
    write_json("recommend_empty.json", {"recommendations": [], "fallback_used": False})

    build_chat_fixtures(client, headers)

    # --- Errors ---------------------------------------------------------------
    # A well-formed token pointing at an account that isn't in the DB → 404.
    # (A missing/expired/garbled token is the 401 case instead — see the
    # UNAUTHORIZED mapping in main's error envelope.)
    bogus = {"Authorization": f"Bearer {app_auth.create_access_token('nope')}"}
    write_json(
        "error_not_found.json",
        client.post("/recommend", json={"limit": 50, **TU_RANGSIT}, headers=bogus).json(),
    )
    write_json(
        "error_invalid_prefs.json",
        client.put(
            "/preferences",
            json={"hard": {"allergens": ["moon_dust"]}, "soft": {}},
            headers=headers,
        ).json(),
    )


# The message the chat fixtures are built from — ROADMAP M2's own example.
CHAT_TEXT = "อยากกินอะไรเผ็ดๆ ไม่เอาหมู"


def stub_gemini(*, extract, narrate=None) -> None:
    """Point /chat at canned Gemini answers for the length of this generator.

    Fixtures have to be byte-stable and runnable without a key, and a live model
    is neither. Everything *around* the two calls is the real endpoint: the same
    extraction result is unioned into the same filter, and the cards below came
    out of it untouched. Pass an exception to reproduce an outage.
    """

    def answer(value):
        def call(*args):
            if isinstance(value, Exception):
                raise value
            return value(*args) if callable(value) else value

        return call

    llm_extract.extract = answer(extract)
    llm_narrate.narrate = answer(narrate)


def build_chat_fixtures(client: TestClient, headers: dict) -> None:
    """The three chat states FE builds against (ROADMAP M2, contract handoff)."""
    client.put(
        "/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {"spicy_tolerance": 3}},
        headers=headers,
    )

    # --- Case 1: a reply with cards ------------------------------------------
    # "spicy, no pork" — the message adds `no_pork` on top of the stored peanut
    # allergy, and the filter enforces both.
    detected = llm_extract.ExtractResult(
        cravings=["เผ็ด"],
        hard_constraints=llm_extract.ExtractedHardConstraints(no_pork=True),
        soft_prefs=llm_extract.ExtractedSoftPrefs(spicy_tolerance=3),
    )
    stub_gemini(
        extract=detected,
        # Built from the cards it is handed, so the fixture names real venues —
        # exactly what a grounded reply looks like on the wire.
        narrate=lambda text, cards: (
            f"ลองดู {cards[0].name_th} หรือ {cards[1].name_th} ดูไหมคะ "
            "สองร้านนี้มีเมนูเผ็ดที่ไม่มีหมูอยู่หลายอย่างเลย"
        ),
    )
    with_cards = client.post(
        # Seeded so regenerating the contract doesn't reshuffle tied cards and
        # produce a diff that says nothing.
        "/chat",
        json={"text": CHAT_TEXT, "limit": 50, "seed": 1, **TU_RANGSIT},
        headers=headers,
    ).json()
    assert with_cards["degraded"] is None, "the grounded reply should have survived"
    write_json("chat_with_cards.json", trim(with_cards))

    # --- Case 2: a reply with no cards ---------------------------------------
    # Synthesised for the same reason as `recommend_empty.json`: no profile over
    # the current 50 restaurants comes back empty. The reply is the real constant
    # the server sends in that state.
    write_json(
        "chat_no_cards.json",
        {
            "reply": llm_narrate.NO_RESULTS_REPLY,
            "recommendations": [],
            "session_id": with_cards["session_id"],
            "fallback_used": False,
            "degraded": None,
        },
    )

    # --- Case 3: Gemini unavailable ------------------------------------------
    # A real response through the real degradation path — this is also what a
    # deployment with no GEMINI_API_KEY returns for every message.
    stub_gemini(extract=llm_extract.ExtractUnavailable("Gemini unreachable"))
    degraded = client.post(
        "/chat",
        json={"text": CHAT_TEXT, "limit": 50, "seed": 1, **TU_RANGSIT},
        headers=headers,
    ).json()
    assert degraded["degraded"] == "LLM_UNAVAILABLE"
    assert degraded["recommendations"], "degrading must not empty the results"
    write_json("chat_degraded.json", trim(degraded))


def _fixture_enrichment() -> places.PlaceEnrichment:
    """A representative Place Details response, used to seed the enriched fixture."""
    return places.PlaceEnrichment(
        rating=4.3,
        user_rating_count=215,
        display_name="ร้านอาหารตัวอย่าง",
        formatted_address="99 หมู่ 1 ถนนพหลโยธิน คลองหลวง ปทุมธานี 12120",
        photo_names=["places/ChIJ/fixture/photo/1", "places/ChIJ/fixture/photo/2"],
        opening_hours=[
            "Monday: 10:00 AM – 10:00 PM",
            "Tuesday: 10:00 AM – 10:00 PM",
            "Wednesday: 10:00 AM – 10:00 PM",
            "Thursday: 10:00 AM – 10:00 PM",
            "Friday: 10:00 AM – 11:00 PM",
            "Saturday: 9:00 AM – 11:00 PM",
            "Sunday: 9:00 AM – 10:00 PM",
        ],
        reviews=[
            {
                "author_name": "พลอย",
                "rating": 5,
                "text": "อาหารอร่อยมาก บรรยากาศดี พนักงานบริการเป็นกันเอง แนะนำเลยค่ะ",
                "relative_time": "a month ago",
            },
            {
                "author_name": "Tan",
                "rating": 4,
                "text": "Good food, reasonable prices. Parking can be tight on weekends.",
                "relative_time": "2 months ago",
            },
        ],
    )


def build_restaurant_detail_fixtures(client: TestClient, conn) -> None:
    """Two states the detail screen must render (ROADMAP M4, contract handoff):
    a degraded (keyless, all nulls) response, and an enriched one."""
    row = conn.execute(
        "SELECT id FROM restaurants "
        "WHERE google_place_id IS NOT NULL "
        "ORDER BY (SELECT COUNT(*) FROM menu_items m WHERE m.restaurant_id = restaurants.id) DESC, id "
        "LIMIT 1;"
    ).fetchone()
    rid = row["id"]

    # --- Case 1: keyless (no enrichment) — every Places field is null ---------
    write_json("restaurant_detail.json", client.get(f"/restaurants/{rid}").json())

    # --- Case 2: enriched (seeded cache → real endpoint response) -------------
    places.save_cached(conn, rid, _fixture_enrichment())
    # Fixed far-future synced_at so is_fresh always returns True in the generator
    # and the cached data is served without attempting a real Places fetch.
    conn.execute(
        "UPDATE restaurants SET places_synced_at = ? WHERE id = ?;",
        ("2099-01-01T00:00:00+00:00", rid),
    )
    conn.commit()
    write_json("restaurant_detail_enriched.json", client.get(f"/restaurants/{rid}").json())


def main() -> None:
    DOCS_API.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)

    spec_path = DOCS_API / "openapi.yaml"
    spec_path.write_text(
        "# GENERATED by backend/tools/make_contract.py — do not hand-edit.\n"
        "# Change the pydantic models in backend/app/schemas.py and re-run it.\n"
        + yaml.dump(
            app.openapi(), Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )
    print(f"Wrote {spec_path.relative_to(config.REPO_ROOT)}")

    with tempfile.TemporaryDirectory() as tmp:
        config.DB_PATH = Path(tmp) / "contract.db"
        conn = db.connect(config.DB_PATH)
        try:
            ingest.ingest(conn, config.DATA_DIR)
            with TestClient(app) as client:
                build_fixtures(client)
                build_restaurant_detail_fixtures(client, conn)
        finally:
            conn.close()


if __name__ == "__main__":
    main()