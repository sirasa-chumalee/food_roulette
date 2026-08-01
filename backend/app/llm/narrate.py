"""Step 3 of the sandwich: write the reply (DESIGN §6).

By the time this runs the filter has already chosen. Gemini is handed the
finished cards and asked to introduce them — it cannot add a restaurant,
because the only names it is ever shown are the ones already in the response.

That is the whole guardrail, and it only holds while the client keeps rendering
cards from `recommendations[]` instead of parsing them out of `reply`.
"""
from __future__ import annotations

import re

from .. import config, schemas
from .extract import ExtractTimeout, ExtractUnavailable, _looks_like_timeout

# Nothing survived the filter. There is no venue to describe, so a fixed line is
# both cheaper and impossible to hallucinate from.
NO_RESULTS_REPLY = (
    "I couldn't find anything that fits all your restrictions right now. "
    "Loosening one preference would give me more to work with."
)

_PROMPT = """You introduce restaurant suggestions to a diner, in two sentences.

Rules:
- Mention only restaurants from the list below. Never invent one, and never
  mention a dish that isn't listed under its restaurant.
- Don't promise anything about allergens or ingredients. The app shows that
  separately and it has to stay the only source for it.
- Reply in the language the diner wrote in.
- If a restaurant is marked unverified, say its details still need checking.
"""


def narrate(user_text: str, recommendations: list[schemas.RecommendedRestaurant]) -> str:
    """Turn already-chosen cards into a short reply."""
    if not recommendations:
        return NO_RESULTS_REPLY

    if not config.GEMINI_API_KEY:
        raise ExtractUnavailable("GEMINI_API_KEY is not set")

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=config.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_MS),
    )

    # Deliberately narrow: names, tier, a few dish names. Anything the filter
    # rejected is not in this structure and so cannot be talked about.
    grounding = [
        {
            "name": card.name_th or card.name_en or card.restaurant_id,
            "safety_tier": card.safety_tier,
            "dishes": [d.name_th or d.name_en for d in card.safe_dishes[:5]],
        }
        for card in recommendations[:5]
    ]

    prompt = f"{_PROMPT}\nDiner said: {user_text}\n\nRestaurants: {grounding}\n"

    try:
        response = client.models.generate_content(
            model=config.GEMINI_NARRATE_MODEL,
            contents=prompt,
            # Low, not zero: this is the one step where a little phrasing variety
            # reads better, and nothing here is safety-critical.
            config=types.GenerateContentConfig(temperature=0.2),
        )
    except Exception as exc:
        if _looks_like_timeout(exc):
            raise ExtractTimeout(str(exc)) from exc
        raise ExtractUnavailable(str(exc)) from exc

    if not response.text:
        raise ExtractUnavailable("Gemini returned an empty reply")
    return response.text.strip()


# Restaurant ids in this dataset all look like `tu_place_12`. A reply has no
# reason to contain one at all, but if it does it must be one we returned.
_ID_PATTERN = re.compile(r"\btu_place_\d+\b")

# Below this, a "name" is too short to match on without tripping over ordinary
# words — an exclusion this narrow costs nothing and avoids false alarms.
_MIN_NAME_LEN = 3


def ungrounded_mentions(
    reply: str,
    recommendations: list[schemas.RecommendedRestaurant],
    other_names: list[str] | None = None,
) -> list[str]:
    """Restaurants the reply names that aren't in `recommendations`.

    Two things are checkable without guessing: a restaurant **id** that isn't in
    the response, and the **name** of a real restaurant we deliberately didn't
    return (`other_names`, i.e. one the filter or the ranking dropped). Both mean
    the prose is pointing somewhere the cards don't go.

    A name invented from nothing is not detectable here, and doesn't need to be:
    the client renders cards from `recommendations`, never from `reply`
    (DESIGN §6). This function catches the case that *would* mislead — the model
    steering someone toward a venue the safety filter already rejected.
    """
    returned_ids = {card.restaurant_id for card in recommendations}
    returned_names = [
        name
        for card in recommendations
        for name in (card.name_th, card.name_en)
        if name
    ]

    offenders = [
        found for found in _ID_PATTERN.findall(reply) if found not in returned_ids
    ]

    for name in other_names or []:
        if len(name) < _MIN_NAME_LEN or name not in reply:
            continue
        # "CO" is a whole restaurant here and also sits inside "CO Coffee &
        # Restaurant". If the match is only there because it's part of a name we
        # *did* return, the reply never left the list.
        if any(name in returned for returned in returned_names):
            continue
        offenders.append(name)

    return offenders
