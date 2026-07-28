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
