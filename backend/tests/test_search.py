"""Search: the FTS5 index built from descriptions must be queryable."""

import json
import uuid

import pytest

from app import config, db, ingest, search
from app.llm import extract as llm_extract
from app.llm import narrate as llm_narrate

MENU = [
    {
        "id": 1, "restaurant_id": "tu_place_1", "name_th": "กาแฟดำ", "name_en": "Black Coffee",
        "category": None, "price_thb": 60, "spicy_level": 0, "confidence": "high",
        "crustaceans": 0, "fish": 0, "milk": 0, "eggs": 0, "peanuts": 0, "tree_nuts": 0,
        "wheat": 1, "soy": 0, "sesame": 0, "molluscs": 0, "contains_meat": 0,
        "contains_pork": 0, "contains_beef": 0, "contains_alcohol": 0,
        "contains_pungent_veg": 0, "is_vegetarian": 1, "is_vegan": 1,
        "is_pescatarian": 1, "is_jay": 1,
    },
    {
        "id": 2, "restaurant_id": "tu_place_2", "name_th": "ก๋วยเตี๋ยว", "name_en": "Noodle",
        "category": "Main", "price_thb": 8.0, "spicy_level": 2, "confidence": "low",
        "crustaceans": 0, "fish": 0, "milk": 0, "eggs": 0, "peanuts": 0, "tree_nuts": 0,
        "wheat": 1, "soy": 0, "sesame": 0, "molluscs": 0, "contains_meat": 1,
        "contains_pork": 1, "contains_beef": 0, "contains_alcohol": 0,
        "contains_pungent_veg": 0, "is_vegetarian": 0, "is_vegan": 0,
        "is_pescatarian": 0, "is_jay": 0,
    },
]


def _make_fixture(tmp_path):
    restaurants = [
        {
            "id": "tu_place_1", "google_place_id": None, "name_th": "Swan Lake",
            "name_en": None, "latitude": 14.0, "longitude": 100.0, "price_band": None,
            "is_halal_certified": 0, "has_parking": 2,
            "description": "Quiet lakeside cafe known for hand-dripped coffee.",
        },
        {
            "id": "tu_place_2", "google_place_id": None, "name_th": "Noodle Corner",
            "name_en": None, "latitude": 13.9, "longitude": 100.1, "price_band": None,
            "is_halal_certified": 0, "has_parking": 2,
            "description": "Bustling riverside noodle stall with spicy broth.",
        },
    ]
    (tmp_path / "restaurants.json").write_text(json.dumps(restaurants), encoding="utf-8")
    (tmp_path / "menu_items.json").write_text(json.dumps(MENU), encoding="utf-8")


def _conn(tmp_path):
    _make_fixture(tmp_path)
    conn = db.connect(tmp_path / "test.db")
    ingest.ingest(conn, tmp_path)
    search.build_index(conn)
    return conn


def test_match_returns_restaurant_mentioned_in_description(tmp_path):
    conn = _conn(tmp_path)
    try:
        ids = search.match_restaurant_ids(conn, ["lakeside"])
        assert "tu_place_1" in ids
    finally:
        conn.close()


def test_match_is_case_insensitive_and_word_scoped(tmp_path):
    conn = _conn(tmp_path)
    try:
        ids = search.match_restaurant_ids(conn, ["CAFE"])
        assert "tu_place_1" in ids
        # "pa" is a substring of "parking"/"riverside"? No — FTS5 is word-scoped.
        ids = search.match_restaurant_ids(conn, ["ri"])
        assert "tu_place_2" not in ids
    finally:
        conn.close()


def test_match_across_multiple_phrases_is_and(tmp_path):
    conn = _conn(tmp_path)
    try:
        # Both words must appear together to hit, else empty.
        assert "tu_place_1" in search.match_restaurant_ids(conn, ["lakeside cafe"])
        assert search.match_restaurant_ids(conn, ["lakeside noodle"]) == set()
    finally:
        conn.close()


def test_separate_phrases_are_ored_not_anded(tmp_path):
    conn = _conn(tmp_path)
    try:
        # A craving phrase and a facility-need phrase are independent asks
        # (main.py concatenates extract.py's cravings + facility_needs into one
        # list). Requiring both words to co-occur in one restaurant's text
        # would demand "cafe" and "noodle" appear together, matching nothing —
        # each phrase should instead credit whichever restaurant it hits on
        # its own, and the results union.
        ids = search.match_restaurant_ids(conn, ["cafe", "noodle"])
        assert ids == {"tu_place_1", "tu_place_2"}
    finally:
        conn.close()


def test_thai_compound_phrase_matches_via_substring_fallback(tmp_path):
    conn = _conn(tmp_path)
    try:
        # Thai has no spaces between words, so a craving like "อาหารอินเดีย"
        # (Indian food) arrives from extract.py as one glued token — FTS5's
        # tokenizer can't split it, so the token match alone would miss a
        # restaurant whose description literally contains that exact
        # substring. The LIKE fallback must still find it.
        restaurant_id = "tu_place_1"
        conn.execute(
            "UPDATE restaurants SET description = ? WHERE id = ?;",
            ("เป็นร้านอาหารอินเดียต้นตำรับแท้ๆ ในราคานักศึกษา", restaurant_id),
        )
        search.build_index(conn)
        ids = search.match_restaurant_ids(conn, ["อาหารอินเดีย"])
        assert restaurant_id in ids
    finally:
        conn.close()


def test_thai_fallback_does_not_apply_to_latin_phrases(tmp_path):
    conn = _conn(tmp_path)
    try:
        # The substring fallback is scoped to phrases containing Thai script.
        # A short Latin phrase must stay word-scoped via FTS only, or "ri"
        # would substring-hit "riverside" the same way the guarded test above
        # proves it must not.
        ids = search.match_restaurant_ids(conn, ["ri"])
        assert ids == set()
    finally:
        conn.close()


def test_match_surfaces_dish_names_too(tmp_path):
    conn = _conn(tmp_path)
    try:
        # "coffee" is only in the dishes (name_en) of tu_place_1, not the desc.
        ids = search.match_restaurant_ids(conn, ["coffee"])
        assert "tu_place_1" in ids
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Cuisine/craving search ("chinese food" bug report).
#
# No dish is cuisine-tagged, so a bare cuisine word like "chinese food" shares
# no literal word with the Thai dish text and matches nothing on its own —
# real Chinese-fusion restaurants exist (SEEFAH, TingTing) but search.py can't
# find them from that word alone. Fixed at the extraction prompt (extract.py):
# Gemini is asked to add real Thai dish/ingredient keywords whenever it detects
# a cuisine craving, so search.py stays a plain deterministic matcher — no
# hardcoded restaurant-to-cuisine table. Tests below prove two separate things:
# 1) given the kind of keywords Gemini should produce, the existing matcher
#    (unchanged) correctly finds the right restaurants, and 2) that value
#    reaches an actual /chat response. Prompt compliance itself is only
#    checkable against the real model — see the opt-in test at the bottom.
# ---------------------------------------------------------------------------

TU_RANGSIT = {"latitude": 14.0700, "longitude": 100.6040}

# Verified Chinese-cuisine matches: SEEFAH/TingTing say so in their own
# description; the other three serve wonton/roast-duck/dumpling dishes.
CHINESE_IDS = {"tu_place_14", "tu_place_23", "tu_place_31", "tu_place_35", "tu_place_41"}
CHINESE_KEYWORDS = ["เกี๊ยว", "หมูแดง", "เป็ดย่าง", "ติ่มซำ"]


def test_decomposed_chinese_keywords_match_real_chinese_restaurants(conn):
    """If Gemini follows the prompt and adds these keywords, they must resolve
    to real restaurants — pins the matcher side of the fix, independent of
    whether Gemini actually cooperates."""
    matched = search.match_restaurant_ids(conn, CHINESE_KEYWORDS)
    assert matched & CHINESE_IDS, f"{CHINESE_KEYWORDS!r} matched none of {CHINESE_IDS}"


@pytest.mark.parametrize(
    "keywords,expect_any_of",
    [
        (["ญี่ปุ่น", "ซูชิ", "ราเมน"], {"tu_place_28", "tu_place_38"}),
        (["เกาหลี", "กิมจิ"], {"tu_place_32"}),
        (["อิตาเลียน", "พาสต้า"], {"tu_place_48"}),
        (["ทะเล", "กุ้ง", "หอย"], {"tu_place_1", "tu_place_31"}),
    ],
)
def test_decomposed_keywords_match_a_real_restaurant_for_other_cuisines(
    conn, keywords, expect_any_of
):
    matched = search.match_restaurant_ids(conn, keywords)
    assert matched & expect_any_of, f"{keywords!r} matched none of {expect_any_of}"


# --- Integration: prove the fix shows up in an actual /chat response, given
# extraction output shaped like the new prompt asks for.


@pytest.mark.parametrize("text", ["I want chinese food", "อยากกินอาหารจีนอร่อยๆ"])
def test_chinese_craving_surfaces_real_cards_through_chat(client, user, monkeypatch, text):
    """Given cravings shaped like the new prompt should produce, /chat must
    rank real Chinese-cuisine restaurants to the top. Identity comes from the
    registered+logged-in `user` fixture (bearer header), never a body field."""
    cravings = ["chinese food", *CHINESE_KEYWORDS]
    monkeypatch.setattr(
        llm_extract, "extract", lambda t: llm_extract.ExtractResult(cravings=cravings)
    )
    monkeypatch.setattr(llm_narrate, "narrate", lambda t, cards: "ลองดูร้านพวกนี้นะคะ")

    response = client.post(
        "/chat",
        json={"text": text, "limit": 5, **TU_RANGSIT},
        headers=user["headers"],
    )
    assert response.status_code == 200, response.text
    body = response.json()

    top_ids = [c["restaurant_id"] for c in body["recommendations"]]
    hits = set(top_ids) & CHINESE_IDS
    assert len(hits) >= 4, f"expected most of the top 5 to be Chinese-cuisine, got {top_ids}"


# --- Opt-in live check: does the real model actually follow the new prompt
# instruction? Only this test can answer that — everything above stubs
# extraction, so it would pass even if Gemini ignored the instruction
# entirely. Skipped unless a real key is set, and never runs by default.


@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="requires a real GEMINI_API_KEY")
def test_real_model_adds_thai_keywords_for_a_cuisine_craving():
    result = llm_extract.extract("I want chinese food")
    assert any(search._HAS_THAI.search(c) for c in result.cravings), (
        f"expected at least one Thai keyword among cravings, got {result.cravings!r}"
    )
