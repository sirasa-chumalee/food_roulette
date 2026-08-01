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
import sys
import tempfile
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db, ingest  # noqa: E402
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


def build_fixtures(client: TestClient) -> None:
    health = client.get("/health").json()
    # The live value is whatever DB this generator ran against — a temp path
    # that would be noise (and machine-specific churn) in a committed fixture.
    health["db"] = "backend/food_roulette.db"
    write_json("health.json", health)

    session = client.post("/auth/session", json={"display_name": "Ploy"}).json()
    write_json("auth_session.json", session)
    user_id = session["user_id"]

    prefs = {
        "hard": {"allergens": ["peanuts", "shellfish"], "halal": True},
        "soft": {"spicy_tolerance": 2, "price_tier": "$$", "diet_style": "none"},
    }
    write_json(
        "preferences.json", client.put(f"/users/{user_id}/preferences", json=prefs).json()
    )

    # --- Case 1: all verified -------------------------------------------------
    # A peanut + shellfish allergy with halal still leaves every restaurant with
    # high-confidence safe dishes — this is the normal, happy path.
    all_verified = client.post(
        "/recommend", json={"user_id": user_id, "limit": 50, **TU_RANGSIT}
    ).json()
    assert all(c["safety_tier"] == "verified" for c in all_verified["recommendations"])
    write_json("recommend_all_verified.json", trim(all_verified))

    # --- Case 2: mixed --------------------------------------------------------
    # Jain is the one real constraint in this dataset that leaves a restaurant
    # with only low-confidence dishes, so the response carries both tiers.
    client.put(f"/users/{user_id}/preferences", json={"hard": {"jain": True}, "soft": {}})
    mixed_full = client.post(
        "/recommend", json={"user_id": user_id, "limit": 50, **TU_RANGSIT}
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

    build_chat_fixtures(client, user_id)

    # --- Errors ---------------------------------------------------------------
    write_json(
        "error_not_found.json",
        client.post("/recommend", json={"user_id": "nope", **TU_RANGSIT}).json(),
    )
    write_json(
        "error_invalid_prefs.json",
        client.put(
            f"/users/{user_id}/preferences",
            json={"hard": {"allergens": ["moon_dust"]}, "soft": {}},
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


def build_chat_fixtures(client: TestClient, user_id: str) -> None:
    """The three chat states FE builds against (ROADMAP M2, contract handoff)."""
    client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {"spicy_tolerance": 3}},
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
        json={"user_id": user_id, "text": CHAT_TEXT, "limit": 50, "seed": 1, **TU_RANGSIT},
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
        json={"user_id": user_id, "text": CHAT_TEXT, "limit": 50, "seed": 1, **TU_RANGSIT},
    ).json()
    assert degraded["degraded"] == "LLM_UNAVAILABLE"
    assert degraded["recommendations"], "degrading must not empty the results"
    write_json("chat_degraded.json", trim(degraded))


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
        finally:
            conn.close()

        with TestClient(app) as client:
            build_fixtures(client)


if __name__ == "__main__":
    main()
