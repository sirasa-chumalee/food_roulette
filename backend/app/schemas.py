"""Request/response models for the M1 endpoints. See docs/DESIGN.md §3-5.

These classes *are* the API contract: `docs/api/openapi.yaml` and the fixtures in
`docs/api/fixtures/` are generated from them, and the Flutter models mirror them.
Renaming or removing a field here is a breaking contract change (ROADMAP §1,
Rule 3) — adding an optional one is not.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Allergen = Literal[
    "peanuts", "tree_nuts", "shellfish", "fish", "wheat", "soy", "milk", "eggs", "sesame"
]


class HardConstraints(BaseModel):
    """Non-negotiable rules. Every one of these is enforced in SQL by
    `filter.py` — the LLM never gets a say (DESIGN §4)."""

    allergens: list[Allergen] = []
    halal: bool = False
    no_beef: bool = False
    # Standalone pork avoidance. Halal implies it, but plenty of people skip pork
    # without keeping halal, and "ไม่เอาหมู" is one of the commonest things a
    # diner types — it needs somewhere to land that isn't a religious flag.
    no_pork: bool = False
    vegetarian: bool = False
    vegan: bool = False
    jain: bool = False
    jay: bool = False  # Thai เจ: vegan + no pungent vegetables
    celiac: bool = False


class SoftPreferences(BaseModel):
    spicy_tolerance: int = Field(3, ge=0, le=3)
    price_tier: Literal["$", "$$", "$$$", "$$$$"] | None = None
    diet_style: Literal["keto", "low_carb", "mediterranean", "carnivore", "none"] = "none"
    wants_parking: bool = False


class PreferencesIn(BaseModel):
    hard: HardConstraints = HardConstraints()
    soft: SoftPreferences = SoftPreferences()


class PreferencesOut(PreferencesIn):
    user_id: str


class SessionIn(BaseModel):
    display_name: str | None = None


class SessionOut(BaseModel):
    user_id: str
    token: str
    display_name: str | None = None


class RecommendIn(BaseModel):
    user_id: str
    latitude: float | None = None
    longitude: float | None = None
    limit: int = Field(10, ge=1, le=50)
    # Fixes the random tiebreak so an ordering can be replayed — M5's roulette
    # needs a spin to be reproducible. Omit it for a fresh shuffle each call.
    seed: int | None = None


class SafeDish(BaseModel):
    id: int
    name_th: str | None
    name_en: str | None
    price_thb: float | None
    spicy_level: int | None
    safety_tier: Literal["verified", "unverified"]


class RecommendedRestaurant(BaseModel):
    """The single object the whole UI is built from (ROADMAP §3.1).

    `rating` and `photo_url` stay null until M4 wires up Google Places; the
    client must render gracefully without them from day one.
    """

    restaurant_id: str
    name_th: str | None
    name_en: str | None
    latitude: float | None
    longitude: float | None
    distance_m: float | None
    price_tier: str | None
    rating: float | None = None
    photo_url: str | None = None
    safety_tier: Literal["verified", "unverified"]
    needs_ack: bool
    ack_reason: str | None = None
    excluded_count: int
    safe_dishes: list[SafeDish]


class RecommendOut(BaseModel):
    recommendations: list[RecommendedRestaurant]
    fallback_used: bool


# --- Error envelope (ROADMAP §3.2) ------------------------------------------
# Every non-2xx response from this API has this shape, no exceptions. `message`
# is safe to show a user; `detail` is for logs and never carries a stack trace.

ErrorCode = Literal[
    "NO_RESULTS",
    "INVALID_PREFS",
    "NOT_FOUND",
    "LLM_UNAVAILABLE",
    "UPSTREAM_TIMEOUT",
    "INTERNAL",
]


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    detail: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


# --- Chat (M2) --------------------------------------------------------------
# Defined after ErrorCode because ChatOut.degraded reuses it: a Gemini outage is
# reported inside a normal 200 response, not as a failed request.


class ChatIn(BaseModel):
    user_id: str
    text: str
    # Groups one conversation. Omit it on the first message and the server mints
    # one; send it back on every message after that.
    session_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    limit: int = Field(10, ge=1, le=50)
    seed: int | None = None


class ChatOut(BaseModel):
    """Same cards as /recommend, plus the prose that introduces them.

    The client renders cards from `recommendations` and never by reading
    `reply` — that separation is what stops a chatty model from inventing a
    restaurant (DESIGN §6).
    """

    reply: str
    recommendations: list[RecommendedRestaurant]
    session_id: str
    # Same meaning as on RecommendOut: we found something, but nothing verified.
    # Chat renders the identical caution banner, so it needs the identical flag.
    fallback_used: bool = False
    # Set when Gemini was skipped, failed, or wrote something we couldn't ground.
    # The cards are still real — they came from the same filter as /recommend —
    # so this is a note, not an error.
    degraded: ErrorCode | None = None


# --- Restaurant detail (M4 — Google Places) ---------------------------------
# A single photo is a backend URL the client can load directly; the Places key
# never leaves the server (DESIGN §7). Every field is nullable because an
# un-keyed or failed enrichment is a normal, supported state — see places.py.


class PlaceReview(BaseModel):
    author_name: str | None = None
    rating: float | None = None
    text: str | None = None
    relative_time: str | None = None


class PlacesEnrichment(BaseModel):
    rating: float | None = None
    user_rating_count: int | None = None
    display_name: str | None = None
    formatted_address: str | None = None
    photos: list[str] = []          # backend photo URLs, keyless
    opening_hours: list[str] = []
    reviews: list[PlaceReview] = []
    synced_at: str | None = None


class RestaurantDetailOut(BaseModel):
    restaurant: dict
    # The full menu, each dish tagged with its safety tier so the detail screen
    # can show the same verified/unverified badges as the cards (DESIGN §4).
    menu: list[dict]
    safe_dishes: list[SafeDish]
    places: PlacesEnrichment
