"""Search: the FTS5 index built from descriptions must be queryable."""

import json

from app import db, ingest, search

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


def test_match_surfaces_dish_names_too(tmp_path):
    conn = _conn(tmp_path)
    try:
        # "coffee" is only in the dishes (name_en) of tu_place_1, not the desc.
        ids = search.match_restaurant_ids(conn, ["coffee"])
        assert "tu_place_1" in ids
    finally:
        conn.close()