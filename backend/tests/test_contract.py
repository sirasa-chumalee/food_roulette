"""The promises `docs/api/openapi.yaml` and the fixtures make to the Flutter team.

These guard the *shape* of the contract (ROADMAP §3). The deep safety-filter
suite — property tests across all 1250 dishes — is M1's deliverable; the peanut
test at the bottom is only a smoke check that the wiring is live.

Since real JWT auth landed, every protected request here carries the registered
user's bearer token from conftest — identity comes from the token, never a body
field — and a missing/expired token must come back as a 401 UNAUTHORIZED
envelope rather than FastAPI's bare 403 or a raw {"detail": ...}.
"""
from __future__ import annotations

RECOMMENDATION_KEYS = {
    "restaurant_id",
    "name_th",
    "name_en",
    "latitude",
    "longitude",
    "distance_m",
    "price_tier",
    "rating",
    "user_rating_count",
    "photo_url",
    "description",
    "safety_tier",
    "needs_ack",
    "ack_reason",
    "excluded_count",
    "safe_dishes",
}


def test_missing_token_is_unauthorized(client):
    """No Authorization header at all → 401, still inside the error envelope."""
    response = client.get("/preferences")
    assert response.status_code == 401

    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"]
    assert "Traceback" not in body["error"]["message"]


def test_error_envelope_on_unknown_account(client, mint):
    """A well-formed token pointing at an account that doesn't exist → 404."""
    response = client.post(
        "/recommend", json={"limit": 3}, headers=mint("nobody")
    )
    assert response.status_code == 404

    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]
    assert "Traceback" not in body["error"]["message"]


def test_error_envelope_on_unknown_path(client):
    body = client.get("/no/such/route").json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_error_envelope_on_bad_input(client, user):
    """A rejected body must not come back as FastAPI's raw {"detail": [...]}."""
    response = client.put(
        "/preferences",
        json={"hard": {"allergens": ["moon_dust"]}, "soft": {}},
        headers=user["headers"],
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREFS"


def test_preferences_roundtrip(client, user):
    payload = {
        "hard": {"allergens": ["peanuts"], "halal": True},
        "soft": {"spicy_tolerance": 1, "price_tier": "$"},
    }
    put = client.put("/preferences", json=payload, headers=user["headers"])
    assert put.status_code == 200

    got = client.get("/preferences", headers=user["headers"]).json()
    # Identity is stamped from the token, so the saved row belongs to whoever
    # authenticated — no way to read someone else's settings by guessing an id.
    assert got["user_id"] == user["user_id"]
    assert got["hard"]["allergens"] == ["peanuts"]
    assert got["hard"]["halal"] is True
    assert got["soft"]["spicy_tolerance"] == 1


def test_recommendation_object_matches_the_contract(client, user):
    body = client.post(
        "/recommend", json={"limit": 3}, headers=user["headers"]
    ).json()

    assert set(body) == {"recommendations", "fallback_used"}
    assert body["recommendations"], "an unconstrained profile must never come back empty"

    card = body["recommendations"][0]
    assert set(card) == RECOMMENDATION_KEYS
    assert card["safety_tier"] in {"verified", "unverified"}
    # No GOOGLE_PLACES_API_KEY in the test environment, so enrichment_for
    # degrades to nulls here — see test_places.py for the enriched case.
    assert card["rating"] is None
    assert card["photo_url"] is None

    dish = card["safe_dishes"][0]
    assert set(dish) == {"id", "name_th", "name_en", "price_thb", "spicy_level", "safety_tier"}


def test_needs_ack_always_carries_a_reason(client, user):
    """The FE shows `ack_reason` verbatim in the confirm dialog — never blank."""
    client.put(
        "/preferences",
        json={"hard": {"jain": True}, "soft": {}},
        headers=user["headers"],
    )
    body = client.post(
        "/recommend", json={"limit": 50}, headers=user["headers"]
    ).json()

    for card in body["recommendations"]:
        if card["needs_ack"]:
            assert card["safety_tier"] == "unverified"
            assert card["ack_reason"]
        else:
            assert card["ack_reason"] is None


def test_peanut_allergy_smoke_test(client, user, conn):
    """M1 owns the real suite; this only proves the filter is actually wired in."""
    client.put(
        "/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {}},
        headers=user["headers"],
    )
    body = client.post(
        "/recommend", json={"limit": 50}, headers=user["headers"]
    ).json()

    returned_ids = [dish["id"] for card in body["recommendations"] for dish in card["safe_dishes"]]
    assert returned_ids

    peanut_ids = {
        row["id"] for row in conn.execute("SELECT id FROM menu_items WHERE peanuts = 1;")
    }
    assert peanut_ids, "fixture data should contain peanut dishes for this to mean anything"
    assert peanut_ids.isdisjoint(returned_ids)
