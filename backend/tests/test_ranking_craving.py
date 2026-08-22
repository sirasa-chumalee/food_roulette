"""Ranking: a restaurant matching a craving phrase ranks higher (DESIGN §5).

Craving match is, like every other soft signal, **ordering only** — it may never
exclude a restaurant or outrank the safety-confidence bonus. These tests pin
both sides of that.
"""

from __future__ import annotations

from app import ranking
from app.filter import RestaurantDishes, TIER_UNVERIFIED, TIER_VERIFIED
from app.schemas import SoftPreferences


def _candidate(rid: str, tier: str = TIER_VERIFIED) -> ranking.Candidate:
    if tier == TIER_VERIFIED:
        verified = [{"spicy_level": 1, "name_th": "a", "wheat": 0}]
        unverified = []
    else:
        verified = []
        unverified = [{"spicy_level": 2, "name_th": "b", "wheat": 1}]
    dishes = RestaurantDishes(
        restaurant_id=rid,
        verified=verified,
        unverified=unverified,
        total_dishes=1,
    )
    return ranking.Candidate(
        restaurant={"id": rid, "price_band": "$$", "has_parking": 0},
        dishes=dishes,
        distance_m=None,
    )


def test_craving_match_outranks_equal_non_match():
    soft = SoftPreferences(spicy_tolerance=3, price_tier="$$", diet_style="none")
    no_match = _candidate("tu_place_1")
    match = _candidate("tu_place_2")

    ranked = ranking.rank(
        [no_match, match],
        soft,
        craving_matched={"tu_place_2"},
    )
    assert [c.restaurant["id"] for c in ranked] == ["tu_place_2", "tu_place_1"]
    assert ranked[0].score_breakdown["craving"] > 0
    assert ranked[1].score_breakdown.get("craving", 0) == 0


def test_craving_bonus_never_edges_out_verified_safety():
    # A Tier-B restaurant with a craving match must NOT outrank a Tier-A
    # restaurant without one — the verified-safety bonus dominates on purpose.
    safe_tier_a = _candidate("tu_place_a", TIER_VERIFIED)
    craving_tier_b = _candidate("tu_place_b", TIER_UNVERIFIED)
    soft = SoftPreferences(spicy_tolerance=3, price_tier="$$", diet_style="none")

    ranked = ranking.rank(
        [craving_tier_b, safe_tier_a],
        soft,
        craving_matched={"tu_place_b"},
    )
    assert ranked[0].restaurant["id"] == "tu_place_a"