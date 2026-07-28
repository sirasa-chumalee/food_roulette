"""Step 1 of the sandwich: chat text -> typed preferences (DESIGN §6).

This module runs *before* any restaurant is loaded, so nothing it returns can
reach a user without passing the hard filter first. Its output is a *delta* —
things the message asked us to add — never a replacement profile.

Gemini answers into a pydantic model rather than free text, so a malformed
answer is a parse failure we can fall back from, not a string we have to guess
at.
"""
from __future__ import annotations

from pydantic import BaseModel

from .. import config, schemas


class ExtractUnavailable(Exception):
    """Extraction did not happen: no key configured, or Gemini refused/failed.

    Callers treat this as "no delta" and carry on with the stored profile. It is
    never an excuse to skip filtering.
    """


class ExtractTimeout(ExtractUnavailable):
    """Gemini took too long. Separate only so /chat can report the right code."""


class ExtractedHardConstraints(BaseModel):
    """The restrictions a message is allowed to *add*.

    Same field names as `schemas.HardConstraints` so unioning is a plain merge.
    Every field defaults to off: silence means "the user didn't mention it",
    which must never read as "the user lifted it".
    """

    allergens: list[schemas.Allergen] = []
    halal: bool = False
    no_beef: bool = False
    no_pork: bool = False
    vegetarian: bool = False
    vegan: bool = False
    jain: bool = False
    jay: bool = False
    celiac: bool = False


class ExtractedSoftPrefs(BaseModel):
    """Taste, not safety. `None` means the message said nothing about it."""

    spicy_tolerance: int | None = None
    price_tier: str | None = None
    diet_style: str | None = None
    wants_parking: bool | None = None


class ExtractResult(BaseModel):
    cravings: list[str] = []
    hard_constraints: ExtractedHardConstraints = ExtractedHardConstraints()
    soft_prefs: ExtractedSoftPrefs = ExtractedSoftPrefs()
    facility_needs: list[str] = []


_PROMPT = """You read a diner's message and record what they asked for.

Rules:
- Only record something the message actually states or clearly implies.
  Leave everything else at its default. A guess about an allergy is dangerous.
- "ไม่เอาหมู" / "no pork" means `no_pork`, not `halal`. Set `halal` only when
  the message actually asks for halal.
- spicy_tolerance: 0 = not spicy at all, 3 = as spicy as it comes.
- price_tier is one of "$", "$$", "$$$", "$$$$".
- diet_style is one of "keto", "low_carb", "mediterranean", "carnivore", "none".
- cravings are short free-text phrases ("noodles", "something light").
- facility_needs are short free-text phrases ("parking", "quiet").
- Thai and English are both expected. Keep cravings in the language written.

Diner's message:
"""


def extract(text: str) -> ExtractResult:
    """Parse one chat message. Raises rather than returning a partial guess."""
    if not config.GEMINI_API_KEY:
        raise ExtractUnavailable("GEMINI_API_KEY is not set")

    # Imported here so the SDK is only needed when chat is actually configured —
    # the rest of the API runs fine without it installed.
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=config.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_MS),
    )

    try:
        response = client.models.generate_content(
            model=config.GEMINI_EXTRACT_MODEL,
            contents=_PROMPT + text,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=ExtractResult,
            ),
        )
    except Exception as exc:  # SDK raises several unrelated types; all mean "no delta"
        if _looks_like_timeout(exc):
            raise ExtractTimeout(str(exc)) from exc
        raise ExtractUnavailable(str(exc)) from exc

    if response.parsed is None:
        raise ExtractUnavailable("Gemini returned nothing parseable")
    return response.parsed


def _looks_like_timeout(exc: Exception) -> bool:
    # Gemini reports a slow call as 504 DEADLINE_EXCEEDED, which never contains
    # the word "timeout" — matching only that would file every slow call under
    # the wrong code.
    text = str(exc).lower()
    return isinstance(exc, TimeoutError) or "timeout" in text or "deadline" in text


def union_hard_constraints(
    stored: schemas.HardConstraints, detected: ExtractedHardConstraints
) -> schemas.HardConstraints:
    """Add the message's restrictions to the saved ones (DESIGN §6).

    Every field is OR-ed, so this function has no way to switch a restriction
    off. Someone whose profile says "peanut allergy" stays peanut-free even if
    the model decides the message sounded relaxed about it.
    """
    return schemas.HardConstraints(
        allergens=sorted(set(stored.allergens) | set(detected.allergens)),
        halal=stored.halal or detected.halal,
        no_beef=stored.no_beef or detected.no_beef,
        no_pork=stored.no_pork or detected.no_pork,
        vegetarian=stored.vegetarian or detected.vegetarian,
        vegan=stored.vegan or detected.vegan,
        jain=stored.jain or detected.jain,
        jay=stored.jay or detected.jay,
        celiac=stored.celiac or detected.celiac,
    )


_PRICE_TIERS = {"$", "$$", "$$$", "$$$$"}
_DIET_STYLES = {"keto", "low_carb", "mediterranean", "carnivore", "none"}


def union_soft_prefs(
    stored: schemas.SoftPreferences, detected: ExtractedSoftPrefs
) -> schemas.SoftPreferences:
    """Let the message override saved taste settings, for this request only.

    Safe to override — ranking can only reorder, never hide (see ranking.py) —
    and "I want something mild tonight" should beat a profile saved months ago.
    Nothing here is written back to the database.

    Values are checked against what the model allows before use: the prompt asks
    for one of a fixed set, but a model that answers "cheap" instead of "$" must
    fall back to the stored value, not fail the whole request.
    """
    spice = detected.spicy_tolerance
    if spice is None or not 0 <= spice <= 3:
        spice = stored.spicy_tolerance

    price = detected.price_tier if detected.price_tier in _PRICE_TIERS else None
    diet = detected.diet_style if detected.diet_style in _DIET_STYLES else None

    return schemas.SoftPreferences(
        spicy_tolerance=spice,
        price_tier=price or stored.price_tier,
        diet_style=diet or stored.diet_style,
        wants_parking=(
            detected.wants_parking
            if detected.wants_parking is not None
            else stored.wants_parking
        ),
    )
