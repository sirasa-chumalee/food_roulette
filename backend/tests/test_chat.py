"""M2: the chat sandwich (DESIGN §6, ROADMAP M2).

What's actually at stake here isn't the prose — it's that adding a conversation
in front of the recommender didn't open a second path to a dish the filter would
have rejected. So these tests care about three things, in order:

1.  A message can *add* a restriction and never lift one (`union_*`).
2.  Whatever comes back from /chat obeys the hard filter, exactly as /recommend
    does — verified against the dish rows themselves, not against the card.
3.  Gemini failing, timing out, or writing about the wrong restaurant degrades
    to plain recommendations. Chat breaking must not break the product.

Gemini is stubbed throughout: a suite that calls the real API would be slow,
non-deterministic, and would fail on a laptop with no key. The `_no_key` fixture
also guarantees no test can reach the network by accident.
"""
from __future__ import annotations

import pytest

from app import config, schemas
from app.llm import extract as llm_extract
from app.llm import narrate as llm_narrate
from app.main import DEGRADED_REPLY

TU_RANGSIT = {"latitude": 14.0700, "longitude": 100.6040}

HARD_FIELDS = ["halal", "no_beef", "no_pork", "vegetarian", "vegan", "jain", "jay", "celiac"]


@pytest.fixture(autouse=True)
def _no_key(monkeypatch):
    """No test may call Gemini for real, even if the developer exported a key."""
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)


@pytest.fixture()
def stub_llm(monkeypatch):
    """Replace both Gemini calls. `calls` records what extraction was given."""
    calls: list[tuple] = []

    def install(*, extract=None, narrate=None):
        def _extract(text: str):
            calls.append(("extract", text))
            if isinstance(extract, Exception):
                raise extract
            return extract if extract is not None else llm_extract.ExtractResult()

        def _narrate(text: str, recommendations: list):
            calls.append(("narrate", text, [c.restaurant_id for c in recommendations]))
            if isinstance(narrate, Exception):
                raise narrate
            if callable(narrate):
                return narrate(recommendations)
            return narrate if narrate is not None else "Here are a few places."

        monkeypatch.setattr(llm_extract, "extract", _extract)
        monkeypatch.setattr(llm_narrate, "narrate", _narrate)
        return calls

    return install


def chat(client, user_id, text="อยากกินอะไรเผ็ดๆ ไม่เอาหมู", **extra):
    response = client.post(
        "/chat", json={"user_id": user_id, "text": text, "limit": 10, **TU_RANGSIT, **extra}
    )
    assert response.status_code == 200, response.text
    return response.json()


def dish_rows(conn, body: dict) -> list:
    """Every dish the response actually offered, straight from the database."""
    ids = [d["id"] for card in body["recommendations"] for d in card["safe_dishes"]]
    assert ids, "a chat response with cards must offer dishes to check"
    placeholders = ",".join("?" * len(ids))
    return conn.execute(
        f"SELECT * FROM menu_items WHERE id IN ({placeholders});", ids
    ).fetchall()


# ---------------------------------------------------------------------------
# 1. Union — a message adds restrictions, never removes them
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", HARD_FIELDS)
def test_a_silent_message_cannot_switch_off_a_stored_constraint(field):
    """The commonest dangerous failure: the model just doesn't mention it."""
    stored = schemas.HardConstraints(**{field: True})
    merged = llm_extract.union_hard_constraints(stored, llm_extract.ExtractedHardConstraints())
    assert getattr(merged, field) is True


@pytest.mark.parametrize("field", HARD_FIELDS)
def test_a_message_can_add_a_constraint(field):
    detected = llm_extract.ExtractedHardConstraints(**{field: True})
    merged = llm_extract.union_hard_constraints(schemas.HardConstraints(), detected)
    assert getattr(merged, field) is True


def test_stored_allergens_survive_any_extraction():
    stored = schemas.HardConstraints(allergens=["peanuts", "shellfish"])
    merged = llm_extract.union_hard_constraints(
        stored, llm_extract.ExtractedHardConstraints(allergens=["fish"])
    )
    assert set(merged.allergens) == {"peanuts", "shellfish", "fish"}


def test_union_is_never_narrower_than_what_was_stored():
    """Property check over every combination of a stored and a detected flag.

    `union` has one job — the result must satisfy at least everything the stored
    profile did — and this asserts it without trusting the field list above to
    stay complete.
    """
    for stored_field in HARD_FIELDS:
        for detected_field in HARD_FIELDS:
            stored = schemas.HardConstraints(**{stored_field: True})
            detected = llm_extract.ExtractedHardConstraints(**{detected_field: True})
            merged = llm_extract.union_hard_constraints(stored, detected)
            for field in HARD_FIELDS:
                if getattr(stored, field):
                    assert getattr(merged, field), f"{stored_field} lost to {detected_field}"


def test_soft_prefs_may_be_overridden_by_the_message():
    """Taste is allowed to change tonight — ranking can only reorder, not hide."""
    stored = schemas.SoftPreferences(spicy_tolerance=3, price_tier="$$$")
    merged = llm_extract.union_soft_prefs(
        stored, llm_extract.ExtractedSoftPrefs(spicy_tolerance=0, price_tier="$")
    )
    assert merged.spicy_tolerance == 0
    assert merged.price_tier == "$"


def test_junk_soft_prefs_fall_back_to_the_stored_value():
    stored = schemas.SoftPreferences(spicy_tolerance=2, price_tier="$$", diet_style="keto")
    merged = llm_extract.union_soft_prefs(
        stored,
        llm_extract.ExtractedSoftPrefs(spicy_tolerance=99, price_tier="cheap", diet_style="paleo"),
    )
    assert merged.spicy_tolerance == 2
    assert merged.price_tier == "$$"
    assert merged.diet_style == "keto"


# ---------------------------------------------------------------------------
# 2. Safety — the chat path obeys the same filter as /recommend
# ---------------------------------------------------------------------------


def test_a_constraint_detected_in_chat_is_applied(client, conn, user_id, stub_llm):
    """"ไม่เอาหมู" reaches the SQL filter, not just the prompt."""
    stub_llm(extract=llm_extract.ExtractResult(
        cravings=["เผ็ด"],
        hard_constraints=llm_extract.ExtractedHardConstraints(no_pork=True),
    ))

    body = chat(client, user_id)
    assert body["recommendations"], "a no-pork profile still has plenty to eat"
    assert all(row["contains_pork"] == 0 for row in dish_rows(conn, body))


def test_a_stored_allergy_holds_when_the_model_forgets_it(client, conn, user_id, stub_llm):
    client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {}},
    )
    # The model returns nothing at all — the profile is the only thing standing
    # between the user and a peanut.
    stub_llm(extract=llm_extract.ExtractResult())

    body = chat(client, user_id, text="anything is fine honestly")
    assert all(row["peanuts"] == 0 for row in dish_rows(conn, body))


def test_chat_and_recommend_agree_on_the_same_profile(client, user_id, stub_llm):
    """With nothing extracted, chat is /recommend with prose on top."""
    stub_llm(extract=llm_extract.ExtractResult())
    client.put(f"/users/{user_id}/preferences", json={"hard": {"halal": True}, "soft": {}})

    chatted = chat(client, user_id, seed=7)
    recommended = client.post(
        "/recommend", json={"user_id": user_id, "limit": 10, "seed": 7, **TU_RANGSIT}
    ).json()

    assert [c["restaurant_id"] for c in chatted["recommendations"]] == [
        c["restaurant_id"] for c in recommended["recommendations"]
    ]
    assert chatted["fallback_used"] == recommended["fallback_used"]


def test_extraction_is_never_shown_a_restaurant(client, user_id, stub_llm):
    """Step 1 runs before any venue is loaded (DESIGN §6). It gets the message,
    and nothing else — so it has nothing to leak or be steered by."""
    calls = stub_llm(extract=llm_extract.ExtractResult())
    chat(client, user_id, text="ข้าวมันไก่")

    extract_calls = [c for c in calls if c[0] == "extract"]
    assert extract_calls == [("extract", "ข้าวมันไก่")]


def test_narration_only_ever_sees_cards_that_are_in_the_response(client, user_id, stub_llm):
    calls = stub_llm(extract=llm_extract.ExtractResult())
    body = chat(client, user_id)

    (narrate_call,) = [c for c in calls if c[0] == "narrate"]
    assert narrate_call[2] == [c["restaurant_id"] for c in body["recommendations"]]


# ---------------------------------------------------------------------------
# 3. Grounding guardrail — the reply cannot point outside the response
# ---------------------------------------------------------------------------


def test_every_restaurant_id_in_the_reply_exists_in_the_recommendations(
    client, user_id, stub_llm
):
    """ROADMAP M2's guardrail, asserted against the endpoint's own output.

    The narrator is told to name every id it was given plus one it wasn't; the
    shipped reply must still mention no id outside `recommendations`.
    """
    stub_llm(
        extract=llm_extract.ExtractResult(),
        narrate=lambda cards: " ".join(c.restaurant_id for c in cards) + " and tu_place_999",
    )

    body = chat(client, user_id)
    returned = {c["restaurant_id"] for c in body["recommendations"]}
    mentioned = set(llm_narrate._ID_PATTERN.findall(body["reply"]))
    assert mentioned <= returned


def test_a_reply_naming_an_excluded_restaurant_is_discarded(client, user_id, stub_llm):
    """The dangerous case: the model recommends a venue the filter removed."""
    stub_llm(
        extract=llm_extract.ExtractResult(),
        narrate="Skip those and go to tu_place_999 instead.",
    )

    body = chat(client, user_id)
    assert body["reply"] == DEGRADED_REPLY
    assert body["degraded"] == "LLM_UNAVAILABLE"
    # The cards were never in question — only the prose was thrown away.
    assert body["recommendations"]


def test_a_grounded_reply_is_passed_through_untouched(client, user_id, stub_llm):
    stub_llm(
        extract=llm_extract.ExtractResult(),
        narrate=lambda cards: f"{cards[0].name_th} looks like a good fit tonight.",
    )

    body = chat(client, user_id)
    assert body["degraded"] is None
    assert body["recommendations"][0]["name_th"] in body["reply"]


def test_grounding_check_tolerates_a_name_that_contains_another(client, user_id):
    """A returned "CO Coffee & Restaurant" must not trip the check just because
    some other row is called "CO" — a false alarm costs a good reply."""
    card = schemas.RecommendedRestaurant(
        restaurant_id="tu_place_3",
        name_th="CO Coffee & Restaurant",
        name_en=None,
        latitude=None,
        longitude=None,
        distance_m=None,
        price_tier="$$",
        safety_tier="verified",
        needs_ack=False,
        excluded_count=0,
        safe_dishes=[],
    )
    reply = "CO Coffee & Restaurant is open late."

    assert llm_narrate.ungrounded_mentions(reply, [card], ["CO"]) == []
    assert llm_narrate.ungrounded_mentions(reply, [card], ["ครัวแม่หมู มธ."]) == []
    assert llm_narrate.ungrounded_mentions(
        "Try ครัวแม่หมู มธ. instead.", [card], ["ครัวแม่หมู มธ."]
    ) == ["ครัวแม่หมู มธ."]


def test_narration_of_an_empty_result_is_a_fixed_line():
    """Nothing survived, so there is nothing to describe — and nothing to
    hallucinate from. This path never reaches Gemini."""
    assert llm_narrate.narrate("อยากกินอะไรก็ได้", []) == llm_narrate.NO_RESULTS_REPLY


# ---------------------------------------------------------------------------
# 4. Degradation — chat failing must not break the product
# ---------------------------------------------------------------------------


def test_no_api_key_still_returns_recommendations(client, user_id):
    """The default state on a fresh clone: no key, no stub, real code path."""
    body = chat(client, user_id)

    assert body["degraded"] == "LLM_UNAVAILABLE"
    assert body["reply"] == DEGRADED_REPLY
    assert body["recommendations"], "a Gemini outage must not empty the results"
    assert body["session_id"]


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (llm_extract.ExtractUnavailable("down"), "LLM_UNAVAILABLE"),
        (llm_extract.ExtractTimeout("deadline exceeded"), "UPSTREAM_TIMEOUT"),
    ],
)
def test_extraction_failure_degrades_to_the_stored_profile(
    client, conn, user_id, stub_llm, failure, expected
):
    client.put(
        f"/users/{user_id}/preferences",
        json={"hard": {"allergens": ["peanuts"]}, "soft": {}},
    )
    stub_llm(extract=failure)

    body = chat(client, user_id)
    assert body["degraded"] == expected
    assert body["reply"] == DEGRADED_REPLY
    # Degraded means "we couldn't read your message", never "we skipped the filter".
    assert all(row["peanuts"] == 0 for row in dish_rows(conn, body))


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (llm_extract.ExtractUnavailable("refused"), "LLM_UNAVAILABLE"),
        (llm_extract.ExtractTimeout("504 DEADLINE_EXCEEDED"), "UPSTREAM_TIMEOUT"),
    ],
)
def test_narration_failure_keeps_the_cards(client, user_id, stub_llm, failure, expected):
    stub_llm(extract=llm_extract.ExtractResult(), narrate=failure)

    body = chat(client, user_id)
    assert body["degraded"] == expected
    assert body["reply"] == DEGRADED_REPLY
    assert body["recommendations"]


def test_extraction_failure_does_not_attempt_narration(client, user_id, stub_llm):
    """A second call to a service we just watched fail buys a timeout, nothing more."""
    calls = stub_llm(extract=llm_extract.ExtractUnavailable("down"))
    chat(client, user_id)
    assert not [c for c in calls if c[0] == "narrate"]


def test_parsed_cravings_drive_the_search_match(client, user_id, stub_llm, monkeypatch):
    """/chat hands the message's cravings/facility needs to the FTS matcher.

    This is the seam that turns a wish like \"salad, hot\" into a ranking boost:
    the parsed phrases must reach `search.match_restaurant_ids`. The ordering
    bonus itself is pinned in test_ranking_craving.py — here we prove the value
    actually flows end-to-end through /chat.
    """
    seen: dict = {}

    def _fake_match(conn, phrases):
        seen["phrases"] = phrases
        return set()

    monkeypatch.setattr("app.main.search.match_restaurant_ids", _fake_match)
    stub_llm(
        extract=llm_extract.ExtractResult(
            cravings=["salad"],
            facility_needs=["parking"],
        )
    )
    chat(client, user_id, text="crunchy salad, and parking please")

    assert seen == {"phrases": ["salad", "parking"]}


def test_degraded_chat_skips_search_and_still_returns_cards(
    client, user_id, stub_llm, monkeypatch
):
    """Gemini down → no cravings → matcher never called, but cards still come back."""
    hits: list = []
    monkeypatch.setattr(
        "app.main.search.match_restaurant_ids",
        lambda conn, phrases: hits.append(list(phrases)) or set(),
    )
    stub_llm(extract=llm_extract.ExtractUnavailable("down"))
    body = chat(client, user_id)
    assert body["recommendations"]
    assert hits == []


# ---------------------------------------------------------------------------
# 5. Contract shape
# ---------------------------------------------------------------------------


def test_response_matches_the_chat_contract(client, user_id, stub_llm):
    stub_llm(extract=llm_extract.ExtractResult())
    body = chat(client, user_id)

    assert set(body) == {"reply", "recommendations", "session_id", "fallback_used", "degraded"}
    schemas.ChatOut.model_validate(body)


def test_session_id_is_minted_once_and_then_echoed(client, user_id, stub_llm):
    stub_llm(extract=llm_extract.ExtractResult())

    first = chat(client, user_id, text="สวัสดี")
    assert first["session_id"]

    second = chat(client, user_id, text="แล้วอย่างอื่นล่ะ", session_id=first["session_id"])
    assert second["session_id"] == first["session_id"]

    fresh = chat(client, user_id, text="เริ่มใหม่")
    assert fresh["session_id"] != first["session_id"]


def test_unknown_user_gets_the_error_envelope(client):
    response = client.post("/chat", json={"user_id": "nobody", "text": "hi"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_a_malformed_request_gets_the_error_envelope(client, user_id):
    response = client.post("/chat", json={"user_id": user_id, "text": "hi", "limit": 999})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PREFS"
