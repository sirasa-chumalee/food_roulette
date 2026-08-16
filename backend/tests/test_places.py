"""M4 Google Places enrichment tests.

Three guarantees are under test here:

1. The detail + photo endpoints behave, degrade to nulls without a key, and
   never leak the Places key to the client.
2. The lazy/cache accessor (`places.enrichment_for`) reuses fresh cache, degrades
   on failure, and never blocks a detail response.
3. Safety flags always come from our `confidence` data — never from Places.

No test makes a real network call: the keyless path is the real degraded
behaviour, and every keyed path is driven through a stubbed `places.fetch_place`
or `places.fetch_photo_bytes`.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app import config, places, schemas


def _seeded_restaurant(conn):
    """A restaurant id that has a google_place_id, for keyed/enrichment tests."""
    row = conn.execute(
        "SELECT id, google_place_id FROM restaurants "
        "WHERE google_place_id IS NOT NULL ORDER BY id LIMIT 1;"
    ).fetchone()
    assert row is not None
    return row


def _sample_enrichment() -> places.PlaceEnrichment:
    return places.PlaceEnrichment(
        rating=4.5,
        user_rating_count=120,
        display_name="ร้านตัวอย่าง",
        formatted_address="99 หมู่ 1 คลองหลวง ปทุมธานี",
        photo_names=["places/abc/photos/1", "places/abc/photos/2"],
        opening_hours=["จันทร์-ศุกร์: 10:00-22:00"],
        reviews=[
            {
                "author_name": "Ploy",
                "rating": 5,
                "text": "อร่อยมาก",
                "relative_time": "a month ago",
            }
        ],
    )


# --- Keyless degradation (the supported state, DESIGN §7) --------------------


def test_detail_endpoint_shape_without_key(client, conn):
    """No key → a full 200 detail response whose Places fields are all null."""
    rid = _seeded_restaurant(conn)["id"]
    body = client.get(f"/restaurants/{rid}").json()

    assert set(body) == {"restaurant", "menu", "safe_dishes", "places"}
    assert body["restaurant"]["id"] == rid

    # The full menu is tagged with a safety tier derived from our data.
    assert body["menu"], "a restaurant with 25 dishes must not come back menu-less"
    for dish in body["menu"]:
        assert dish["safety_tier"] in {"verified", "unverified"}

    # safe_dishes is the verified (high-confidence) subset only.
    assert body["safe_dishes"], "expected some high-confidence dishes"
    assert all(d["safety_tier"] == "verified" for d in body["safe_dishes"])

    # Every Places field degrades to null/empty when there's no key.
    assert body["places"] == {
        "rating": None,
        "user_rating_count": None,
        "display_name": None,
        "formatted_address": None,
        "photos": [],
        "opening_hours": [],
        "reviews": [],
        "synced_at": None,
    }


def test_detail_endpoint_unknown_restaurant(client):
    body = client.get("/restaurants/does-not-exist").json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_photo_endpoint_unknown_restaurant(client):
    body = client.get("/restaurants/does-not-exist/photos/0").json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_photo_endpoint_without_cached_photos(client, conn):
    """With no enrichment there are no photo handles, so any index is 404."""
    rid = _seeded_restaurant(conn)["id"]
    body = client.get(f"/restaurants/{rid}/photos/0").json()
    assert body["error"]["code"] == "NOT_FOUND"


# --- The lazy + cached accessor ----------------------------------------------


def test_fetch_place_requires_a_key(monkeypatch):
    monkeypatch.setattr(config, "PLACES_API_KEY", None)
    with pytest.raises(places.PlaceForbidden):
        places.fetch_place("ChIJwhatever")


def test_field_mask_paths_are_not_prefixed():
    """The Places API (New) rejects `places.x` field paths with a 400 — the
    mask must use bare field names (the bug that shipped the first keyed run)."""
    fields = [f.strip() for f in places.FIELD_MASK.split(",") if f.strip()]
    assert fields, "field mask must not be empty"
    for field in fields:
        assert not field.startswith("places.")


def test_fetch_photo_bytes_follows_redirects(monkeypatch):
    """The media endpoint answers 302 to the real image — fetch must follow it,
    or we proxy the redirect JSON instead of photo bytes."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    captured = {}

    def _fake_get(url, **kwargs):
        captured["kwargs"] = kwargs
        return httpx.Response(200, content=b"\xff\xd8fake-jpeg")

    monkeypatch.setattr(places.httpx, "get", _fake_get)
    assert places.fetch_photo_bytes("places/x/photos/1") == b"\xff\xd8fake-jpeg"
    assert captured["kwargs"]["follow_redirects"] is True


def test_fetch_photo_bytes_requires_a_key(monkeypatch):
    monkeypatch.setattr(config, "PLACES_API_KEY", None)
    with pytest.raises(places.PlaceForbidden):
        places.fetch_photo_bytes("places/abc/photos/1")


def test_enrichment_for_degrades_to_none_without_key(conn, monkeypatch):
    """No key → enrichment_for returns None rather than raising or blocking."""
    monkeypatch.setattr(config, "PLACES_API_KEY", None)
    rid = _seeded_restaurant(conn)["id"]
    assert places.enrichment_for(conn, rid) is None


def test_enrichment_for_returns_none_for_missing_place_id(conn, monkeypatch):
    """A restaurant with no google_place_id is never enrichment-eligible."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    conn.execute(
        "INSERT INTO restaurants (id, google_place_id, name_th) VALUES (?, NULL, ?);",
        ("no_place", "No Place"),
    )
    conn.commit()
    assert places.enrichment_for(conn, "no_place") is None


def test_enrichment_for_returns_none_for_unknown_restaurant(conn, monkeypatch):
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    assert places.enrichment_for(conn, "does-not-exist") is None


def test_is_fresh_is_false_without_a_synced_at(conn):
    rid = _seeded_restaurant(conn)["id"]
    assert places.is_fresh(conn, rid) is False


def test_save_and_load_cached_roundtrip(conn):
    rid = _seeded_restaurant(conn)["id"]
    enrichment = _sample_enrichment()
    places.save_cached(conn, rid, enrichment)

    loaded = places.load_cached(conn, rid)
    assert loaded is not None
    assert loaded.rating == 4.5
    assert loaded.user_rating_count == 120
    assert loaded.display_name == "ร้านตัวอย่าง"
    assert loaded.photo_names == ["places/abc/photos/1", "places/abc/photos/2"]
    assert loaded.opening_hours == ["จันทร์-ศุกร์: 10:00-22:00"]
    assert loaded.reviews == enrichment.reviews


def test_fresh_cache_is_reused_without_a_fetch(conn, monkeypatch):
    """A fresh cache must win — no network call even with a key present."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]
    places.save_cached(conn, rid, _sample_enrichment())

    def _explode(*args, **kwargs):
        raise AssertionError("fetch_place must not be called when cache is fresh")

    monkeypatch.setattr(places, "fetch_place", _explode)

    cached = places.enrichment_for(conn, rid)
    assert cached is not None
    assert cached.rating == 4.5


def test_failed_fetch_keeps_stale_cache(conn, monkeypatch):
    """A fetch failure must fall back to whatever cache we already have."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]
    places.save_cached(conn, rid, _sample_enrichment())

    # Age the cache out of freshness, then fail the refetch.
    old = datetime.now(timezone.utc) - timedelta(hours=config.PLACES_CACHE_TTL_HOURS + 1)
    conn.execute(
        "UPDATE restaurants SET places_synced_at = ? WHERE id = ?;",
        (old.isoformat(), rid),
    )
    conn.commit()

    def _fail(*args, **kwargs):
        raise places.PlacesTimeout("upstream slow")

    monkeypatch.setattr(places, "fetch_place", _fail)

    cached = places.enrichment_for(conn, rid)
    assert cached is not None
    assert cached.rating == 4.5  # stale-but-real data beats nulls


def test_photo_urls_are_keyless_and_indexed(conn, monkeypatch):
    """Client photo handles are backend paths only — no key, no Google URL."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]
    places.save_cached(conn, rid, _sample_enrichment())

    urls = places.photo_urls(conn, rid)
    assert urls == [f"/restaurants/{rid}/photos/0", f"/restaurants/{rid}/photos/1"]
    for url in urls:
        assert "key=" not in url
        assert "google" not in url.lower()


# --- The photo proxy serves bytes through the backend ------------------------


def test_photo_proxy_returns_proxied_bytes(conn, client, monkeypatch):
    """The proxy fetches by our cached name and returns image bytes to the FE."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]
    places.save_cached(conn, rid, _sample_enrichment())

    seen = {}

    def _fake_fetch(photo_name, max_width=None):
        seen["photo_name"] = photo_name
        seen["max_width"] = max_width
        return b"\xff\xd8fakejpeg"

    monkeypatch.setattr(places, "fetch_photo_bytes", _fake_fetch)

    response = client.get(f"/restaurants/{rid}/photos/1")
    assert response.status_code == 200
    assert response.content == b"\xff\xd8fakejpeg"
    assert response.headers["content-type"].startswith("image/jpeg")
    # The name handed to the (keyed) fetch came from our cache, not the client.
    assert seen["photo_name"] == "places/abc/photos/2"
    assert seen["max_width"] == config.PLACES_MAX_PHOTO_WIDTH


def test_photo_proxy_out_of_range_is_404(conn, client, monkeypatch):
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]
    places.save_cached(conn, rid, _sample_enrichment())

    body = client.get(f"/restaurants/{rid}/photos/9").json()
    assert body["error"]["code"] == "NOT_FOUND"


# --- Safety flags come from our data, never from Places ----------------------


def test_detail_endpoint_reports_synced_at_after_caching(conn, client, monkeypatch):
    """The response's synced_at must reflect a cache written by enrichment_for,
    not a stale snapshot taken before the fetch."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]

    # Simulate a successful fetch-and-cache happening inside enrichment_for by
    # seeding the row the same way save_cached does, then reading it back.
    places.save_cached(conn, rid, _sample_enrichment())

    body = client.get(f"/restaurants/{rid}").json()
    assert body["places"]["rating"] == 4.5
    assert body["places"]["synced_at"] is not None


def test_places_rating_does_not_affect_safety_tier(conn, client, monkeypatch):
    """A fake 5-star Places rating must not flip a Tier-B dish to safe."""
    monkeypatch.setattr(config, "PLACES_API_KEY", "fake-key")
    rid = _seeded_restaurant(conn)["id"]

    # Seed a Places enrichment with a perfect rating for this restaurant.
    places.save_cached(conn, rid, _sample_enrichment())

    # A low-confidence dish is Tier B regardless of the venue's Places rating.
    low = conn.execute(
        "SELECT id FROM menu_items WHERE restaurant_id = ? AND confidence = 'low' LIMIT 1;",
        (rid,),
    ).fetchone()
    high = conn.execute(
        "SELECT id FROM menu_items WHERE restaurant_id = ? AND confidence = 'high' LIMIT 1;",
        (rid,),
    ).fetchone()

    body = client.get(f"/restaurants/{rid}").json()
    menu_by_id = {d["id"]: d for d in body["menu"]}

    if low is not None:
        assert menu_by_id[low["id"]]["safety_tier"] == "unverified"
        assert low["id"] not in {d["id"] for d in body["safe_dishes"]}
    if high is not None:
        assert menu_by_id[high["id"]]["safety_tier"] == "verified"
        assert high["id"] in {d["id"] for d in body["safe_dishes"]}

    # And the Places rating itself is just data — surfaced, never trusted for safety.
    assert body["places"]["rating"] == 4.5
