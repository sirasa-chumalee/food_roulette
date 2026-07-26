"""Request/response models for the M1 endpoints. See docs/DESIGN.md §3-5."""
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
    restaurant_id: str
    name_th: str | None
    name_en: str | None
    distance_m: float | None
    price_tier: str | None
    safety_tier: Literal["verified", "unverified"]
    needs_ack: bool
    excluded_count: int
    safe_dishes: list[SafeDish]


class RecommendOut(BaseModel):
    recommendations: list[RecommendedRestaurant]
    fallback_used: bool
