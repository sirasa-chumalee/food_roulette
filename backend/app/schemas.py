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
    allergens: list[Allergen] = []
    halal: bool = False
    no_beef: bool = False
    vegetarian: bool = False
    vegan: bool = False
    jain: bool = False
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
