"""Request/response models for the M1 endpoints. See docs/DESIGN.md §3-5.

These classes *are* the API contract: `docs/api/openapi.yaml` and the fixtures in
`docs/api/fixtures/` are generated from them, and the Flutter models mirror them.
Renaming or removing a field here is a breaking contract change (ROADMAP §1,
Rule 3) — adding an optional one is not.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, EmailStr

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
    # None means "no stated preference" — ranking.py's _spice_penalty treats
    # None as zero penalty. A non-null default here would silently apply a
    # spice constraint to every user who never touched the Profile screen,
    # penalizing every mild-food restaurant (cafes, dessert places) by
    # default even when nothing was ever asked for.
    spicy_tolerance: int | None = Field(None, ge=0, le=3)
    price_tier: Literal["$", "$$", "$$$", "$$$$"] | None = None
    diet_style: Literal["keto", "low_carb", "mediterranean", "carnivore", "none"] = "none"
    wants_parking: bool = False


class PreferencesIn(BaseModel):
    hard: HardConstraints = HardConstraints()
    soft: SoftPreferences = SoftPreferences()


class PreferencesOut(PreferencesIn):
    user_id: str


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    # The authenticated user, so the client doesn't have to decode the JWT to
    # know who it is (or to address /preferences without re-decoding).
    user_id: str


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str | None
    created_at: str


class RecommendIn(BaseModel):
    # Identity comes from the bearer token (auth.get_current_user_id), never
    # from the body — see main.recommend.
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

    `rating` / `user_rating_count` / `photo_url` come from Google Places
    (M4, lazy + cached server-side — see places.py); they stay null when the
    venue is un-keyed or the lookup failed, and the client must render
    gracefully without them.

    `description` is the human-written, searchable blurb (display only — it is
    never read by filter.py, so it can never become a safety claim).
    """

    restaurant_id: str
    name_th: str | None
    name_en: str | None
    latitude: float | None
    longitude: float | None
    distance_m: float | None
    price_tier: str | None
    rating: float | None = None
    user_rating_count: int | None = None
    photo_url: str | None = None
    description: str | None = None
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
    "UNAUTHORIZED",
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
    # Identity comes from the bearer token (auth.get_current_user_id), never
    # from the body — see main.chat.
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
