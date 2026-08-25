"""M3 history and feedback-loop tests.

These tests use the `client`/`user`/`conn` fixtures from conftest.py. Every
request to the protected /history endpoints carries the authenticated user's
bearer token — identity comes from the token, never the body or a query param,
so none of these tests may send a `user_id` alongside the events.
"""
import uuid

from app import ranking


def _restaurant_id(conn) -> str:
    row = conn.execute("SELECT id FROM restaurants ORDER BY id LIMIT 1;").fetchone()
    assert row is not None
    return row["id"]


def test_post_history_accepts_batch(client, user, conn):
    restaurant_id = _restaurant_id(conn)
    response = client.post(
        "/history",
        headers=user["headers"],
        json={
            "events": [
                {
                    "session_id": "session-a",
                    "restaurant_id": restaurant_id,
                    "action_type": "IMPRESSION",
                    "context": {"source": "recommend", "position": 0},
                },
                {
                    "session_id": "session-a",
                    "restaurant_id": restaurant_id,
                    "action_type": "CLICK",
                    "context": {"source": "card"},
                },
                {
                    "session_id": "session-a",
                    "restaurant_id": restaurant_id,
                    "action_type": "SPIN",
                    "context": {"seed": 123},
                },
                {
                    "session_id": "session-a",
                    "restaurant_id": restaurant_id,
                    "action_type": "REJECTION",
                    "context": {"reason": "not_interested"},
                },
            ],
        },
    )

    assert response.status_code == 201
    assert response.json() == {"accepted": 4}

    rows = conn.execute(
        "SELECT action_type, session_id, context FROM action_history "
        "WHERE user_id = ? ORDER BY id;",
        (user["user_id"],),
    ).fetchall()
    assert [row["action_type"] for row in rows] == [
        "IMPRESSION",
        "CLICK",
        "SPIN",
        "REJECTION",
    ]
    assert rows[-1]["session_id"] == "session-a"
    assert '"reason":"not_interested"' in rows[-1]["context"]


def test_get_history_returns_newest_first(client, user, conn):
    restaurant_id = _restaurant_id(conn)
    client.post(
        "/history",
        headers=user["headers"],
        json={
            "events": [
                {
                    "session_id": "session-a",
                    "restaurant_id": restaurant_id,
                    "action_type": "CLICK",
                },
                {
                    "session_id": "session-b",
                    "restaurant_id": restaurant_id,
                    "action_type": "REJECTION",
                },
            ],
        },
    )

    response = client.get("/history", headers=user["headers"])
    assert response.status_code == 200
    history = response.json()["history"]
    assert [event["action_type"] for event in history] == ["REJECTION", "CLICK"]
    assert history[0]["session_id"] == "session-b"


def test_history_isolated_by_user(client, user, another_user, conn):
    """One account's history must never leak into another's — even between two
    users registered back-to-back against the same database."""
    restaurant_id = _restaurant_id(conn)

    client.post(
        "/history",
        headers=user["headers"],
        json={
            "events": [{
                "session_id": "session-a",
                "restaurant_id": restaurant_id,
                "action_type": "REJECTION",
            }],
        },
    )

    response = client.get("/history", headers=another_user["headers"])
    assert response.status_code == 200
    assert response.json()["history"] == []


def test_unknown_user_gets_not_found(client, mint):
    """A token that decodes but points at an account that doesn't exist."""
    response = client.get("/history", headers=mint("does-not-exist"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_restaurant_rejects_entire_batch(client, user):
    response = client.post(
        "/history",
        headers=user["headers"],
        json={
            "events": [{
                "session_id": "session-a",
                "restaurant_id": "does-not-exist",
                "action_type": "CLICK",
            }],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_empty_history_batch_is_invalid(client, user):
    response = client.post(
        "/history",
        headers=user["headers"],
        json={"events": []},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREFS"


def test_invalid_action_type_is_rejected(client, user, conn):
    restaurant_id = _restaurant_id(conn)
    response = client.post(
        "/history",
        headers=user["headers"],
        json={
            "events": [{
                "session_id": "session-a",
                "restaurant_id": restaurant_id,
                "action_type": "BANANA",
            }],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREFS"


def test_rejection_penalty_is_only_session_scoped():
    # Unit-level proof of the M3 ranking rule: the same candidate is penalized
    # only when its restaurant id appears in the supplied session rejection set.
    from types import SimpleNamespace

    dishes = SimpleNamespace(
        offered_dishes=[{"id": 1, "spicy_level": 1, "contains_meat": 1}],
        safety_tier=ranking.TIER_VERIFIED,
    )
    soft = SimpleNamespace(
        spicy_tolerance=None,
        price_tier=None,
        diet_style="none",
        wants_parking=False,
    )

    candidate = ranking.Candidate(
        restaurant={"id": "r1", "price_band": "$$", "has_parking": 2},
        dishes=dishes,
        distance_m=None,
    )

    normal = ranking.rank([candidate], soft, seed=1)
    normal_score = normal[0].score

    rejected = ranking.rank(
        [candidate],
        soft,
        seed=1,
        rejected_restaurant_ids={"r1"},
    )

    assert rejected[0].score == normal_score - ranking.REJECTION_PENALTY
    assert rejected[0].score_breakdown["rejection"] == -ranking.REJECTION_PENALTY

    not_rejected = ranking.rank([candidate], soft, seed=1, rejected_restaurant_ids={"other"})
    assert not_rejected[0].score == normal[0].score
