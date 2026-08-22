"""Soft-preference ranking (DESIGN §5).

Ordering only. **Nothing in this module may exclude a restaurant** — by the time
a candidate arrives here it has already passed the hard filter, and every dish
attached to it is safe to eat. A low score means "shown further down", never
"hidden".

Scores are unbounded sums of small signed terms, so they're only meaningful
relative to each other within one request. The one term that dominates by design
is `VERIFIED_BONUS`: a Tier-A restaurant always outranks a Tier-B one, whatever
the other preferences say (DESIGN §4).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from . import pricing
from .filter import TIER_VERIFIED, RestaurantDishes
from .schemas import SoftPreferences

# --- Weights ---------------------------------------------------------------
# Deliberately small and hand-tunable. Distance is the reference unit: 1.0 point
# ≈ 1 km of walking, and every other term is priced against that.

VERIFIED_BONUS = 100.0  # dominant on purpose — safety confidence outranks taste
SPICE_WEIGHT = 1.5  # per level of mismatch with the closest safe dish
PRICE_WEIGHT = 2.0  # per band away from the preferred tier
DIET_WEIGHT = 2.0  # scaled by the fraction of safe dishes matching the style
DISTANCE_WEIGHT = 1.0  # per kilometre
PARKING_BONUS = 0.5  # only when the user asked and the venue is known to have it
REJECTION_PENALTY = 5.0  # M3: session-scoped feedback only reorders, never filters
# Keyword match against a craving/facility phrase (DESIGN §5, FTS index). Must
# stay far below VERIFIED_BONUS (100.0) so a Tier-B craving match can never
# outrank a Tier-A restaurant that lacks the match.
CRAVING_BONUS = 4.0

# Thai dish names that signal a carbohydrate base. `category` is empty across the
# whole dataset (ROADMAP §6), so the name is the only carb signal available —
# this is a documented stopgap, not a lasting model of the cuisine.
_CARB_PREFIXES = ("ข้าว", "เส้น", "ก๋วยเตี๋ยว", "บะหมี่", "ผัดไทย", "ขนมปัง", "โรตี", "สปาเก")


def _looks_carby(dish: dict) -> bool:
    name = (dish.get("name_th") or "").strip()
    return dish.get("wheat") == 1 or name.startswith(_CARB_PREFIXES)


# Each style is a predicate over a single safe dish; the restaurant's bonus is
# the fraction of its offered dishes that match. Approximations over the flags we
# actually have — there is no macro data in this dataset.
DIET_STYLE_MATCHERS = {
    "keto": lambda d: not _looks_carby(d),
    "low_carb": lambda d: not _looks_carby(d),
    "carnivore": lambda d: d.get("contains_meat") == 1,
    "mediterranean": lambda d: d.get("fish") == 1 or d.get("is_vegetarian") == 1,
    "none": None,
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres. Coordinates are already local — this
    never costs an API call (DESIGN §5)."""
    earth_radius_m = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * earth_radius_m * math.asin(math.sqrt(a))


@dataclass
class Candidate:
    """A filtered restaurant on its way to becoming a recommendation card."""

    restaurant: dict
    dishes: RestaurantDishes
    distance_m: float | None = None
    score: float = 0.0
    # Per-term breakdown. Costs nothing to keep and turns "why is this fourth?"
    # from an argument into a lookup.
    score_breakdown: dict[str, float] = field(default_factory=dict)


def _spice_penalty(dishes: list[dict], tolerance: int | None) -> float:
    """Distance from the user's tolerance to the *closest* safe dish.

    Scoring the menu average would punish a large menu for containing one mild
    dish; what the user cares about is whether anything here suits them.
    """
    if tolerance is None:
        return 0.0
    levels = [d.get("spicy_level") for d in dishes if d.get("spicy_level") is not None]
    if not levels:
        return 0.0
    return -SPICE_WEIGHT * min(abs(level - tolerance) for level in levels)


def _price_penalty(restaurant: dict, preferred_tier: str | None) -> float:
    if preferred_tier is None:
        return 0.0
    want = pricing.tier_index(preferred_tier)
    have = pricing.tier_index(restaurant.get("price_band"))
    if want is None or have is None:
        return 0.0  # unknown band — no opinion, neither reward nor punish
    return -PRICE_WEIGHT * abs(have - want)


def _diet_bonus(dishes: list[dict], diet_style: str) -> float:
    matcher = DIET_STYLE_MATCHERS.get(diet_style)
    if matcher is None or not dishes:
        return 0.0
    return DIET_WEIGHT * (sum(1 for d in dishes if matcher(d)) / len(dishes))


def _parking_bonus(restaurant: dict, wants_parking: bool) -> float:
    # `has_parking = 2` means *unknown*, not false (ROADMAP §6). An unknown
    # never costs a restaurant its place in the list.
    return PARKING_BONUS if wants_parking and restaurant.get("has_parking") == 1 else 0.0


def score(
    candidate: Candidate,
    soft: SoftPreferences,
    rejected_restaurant_ids: set[str] | None = None,
    craving_matched: set[str] | None = None,
) -> Candidate:
    """Attach a score and its per-term breakdown to one candidate.

    ``rejected_restaurant_ids`` is session-scoped feedback. It can only lower
    ordering; it never removes a candidate and therefore cannot bypass M1
    safety filtering.

    ``craving_matched`` is the set of restaurant ids whose FTS text matched a
    craving/facility phrase. Like every soft signal it is ordering only.
    """
    dishes = candidate.dishes.offered_dishes

    breakdown = {
        "safety": VERIFIED_BONUS if candidate.dishes.safety_tier == TIER_VERIFIED else 0.0,
        "spice": _spice_penalty(dishes, soft.spicy_tolerance),
        "price": _price_penalty(candidate.restaurant, soft.price_tier),
        "diet": _diet_bonus(dishes, soft.diet_style),
        "parking": _parking_bonus(candidate.restaurant, soft.wants_parking),
        "distance": (
            -DISTANCE_WEIGHT * (candidate.distance_m / 1000.0)
            if candidate.distance_m is not None
            else 0.0
        ),
        "rejection": (
            -REJECTION_PENALTY
            if rejected_restaurant_ids and candidate.restaurant.get("id") in rejected_restaurant_ids
            else 0.0
        ),
        "craving": (
            CRAVING_BONUS
            if craving_matched and candidate.restaurant.get("id") in craving_matched
            else 0.0
        ),
    }

    candidate.score_breakdown = breakdown
    candidate.score = sum(breakdown.values())
    return candidate


def rank(
    candidates: list[Candidate],
    soft: SoftPreferences,
    seed: int | None = None,
    rejected_restaurant_ids: set[str] | None = None,
    craving_matched: set[str] | None = None,
) -> list[Candidate]:
    """Score and sort, best first. Ties broken randomly.

    Rejections are supplied by the caller for the current session only.


    ``craving_matched`` is forwarded to ``score`` as the keyword-match set
    (ordering-only bonus). See ``score``.

    The tiebreak is a separate sort key rather than jitter added to the score,
    so it can only reorder genuinely equal candidates — never nudge a worse one
    past a better one. `seed` makes an ordering reproducible, which is what lets
    M5's roulette replay a spin.
    """
    rng = random.Random(seed)
    scored = [
        score(
            candidate,
            soft,
            rejected_restaurant_ids=rejected_restaurant_ids,
            craving_matched=craving_matched,
        )
        for candidate in candidates
    ]
    tiebreak = {id(candidate): rng.random() for candidate in scored}
    scored.sort(key=lambda c: (-c.score, tiebreak[id(c)]))
    return scored
