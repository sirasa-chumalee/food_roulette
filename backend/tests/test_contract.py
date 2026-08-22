"""The promises `docs/api/openapi.yaml` and the fixtures make to the Flutter team.

These guard the *shape* of the contract (ROADMAP §3). The deep safety-filter
suite — property tests across all 1250 dishes — is M1's deliverable; the peanut
test at the bottom is only a smoke check that the wiring is live.
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
    "photo_url",
    "description",
    "safety_tier",
    "needs_ack",
    "ack_reason",
    "excluded_count",
    "safe_dishes",
}


def test_error_envelope_on_unknown_user(client):
    response = client.post("/recommend", json={"user_id": "nobody"})
    assert response.status_code == 404

    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]
    assert "Traceback" not in body["error"]["message"]


def test_error_envelope_on_unknown_path(client):
    body = client.get("/no/such/route").json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_error_envelope_on_bad_input(client, user_id):
    """A rejected body must not come back as FastAPI's raw {"detail": [...]}."""
    response = client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"allergens": ["moon_dust"]}, "soft": {}},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREFS"


def test_preferences_roundtrip(client, user_id):
    payload = {
        "hard": {"allergens": ["peanuts"], "halal": True},
        "soft": {"spicy_tolerance": 1, "price_tier": "$"},
    }
    put = client.put(f"/users/{user_id}/preferences", json=payload)
    assert put.status_code == 200

    got = client.get(f"/users/{user_id}/preferences").json()
    assert got["hard"]["allergens"] == ["peanuts"]
    assert got["hard"]["halal"] is True
    assert got["soft"]["spicy_tolerance"] == 1


def test_recommendation_object_matches_the_contract(client, user_id):
    body = client.post("/recommend", json={"user_id": user_id, "limit": 3}).json()

    assert set(body) == {"recommendations", "fallback_used"}
    assert body["recommendations"], "an unconstrained profile must never come back empty"

    card = body["recommendations"][0]
    assert set(card) == RECOMMENDATION_KEYS
    assert card["safety_tier"] in {"verified", "unverified"}
    # Not enriched until M4 — the FE renders a placeholder for both.
    assert card["rating"] is None
    assert card["photo_url"] is None

    dish = card["safe_dishes"][0]
    assert set(dish) == {"id", "name_th", "name_en", "price_thb", "spicy_level", "safety_tier"}


def test_needs_ack_always_carries_a_reason(client, user_id):
    """The FE shows `ack_reason` verbatim in the confirm dialog — never blank."""
    client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"jain": True}, "soft": {}},
    )
    body = client.post("/recommend", json={"user_id": user_id, "limit": 50}).json()

    for card in body["recommendations"]:
        if card["needs_ack"]:
            assert card["safety_tier"] == "unverified"
            assert card["ack_reason"]
        else:
            assert card["ack_reason"] is None


def test_peanut_allergy_smoke_test(client, user_id, conn):
    """M1 owns the real suite; this only proves the filter is actually wired in."""
    client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {}},
    )
    body = client.post("/recommend", json={"user_id": user_id, "limit": 50}).json()

    returned_ids = [dish["id"] for card in body["recommendations"] for dish in card["safe_dishes"]]
    assert returned_ids

    peanut_ids = {
        row["id"] for row in conn.execute("SELECT id FROM menu_items WHERE peanuts = 1;")
    }
    assert peanut_ids, "fixture data should contain peanut dishes for this to mean anything"
    assert peanut_ids.isdisjoint(returned_ids)
