"""Google Places enrichment for restaurant detail (DESIGN §7, ROADMAP §4 M4).

Three rules shape everything in this module:

1.  **Keyed by `google_place_id`, never by name.** `restaurants.json` already
    ships the resolved Place ID, so enrichment is a direct Place Details call —
    no name search, no geocoding, no ambiguity about *which* venue we mean.

2.  **Lazy + cached.** A restaurant is enriched the first time its detail is
    requested; the result is written back into the `restaurants` row alongside
    `places_synced_at`, and reused until the cache is `PLACES_CACHE_TTL_HOURS`
    old. Distance never waits on Places — lat/lng are already local.

3.  **Keyless / degraded is a supported state.** With no `GOOGLE_PLACES_API_KEY`
    configured, or when a call fails or is slow, every Places field is returned
    as null and the app keeps working, just plainer. A *display* layer must
    never take the whole service down.

**Safety is untouched here.** Allergen/diet flags always come from our data
(the menu_items columns), never from Google. This module only adds
rating/review/photo/hours text. Enforcing "Places never contributes a safety
flag" at the call site is the job of `main.py` and is asserted in tests.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from . import config

# The modern Places API (v1) returns two HTTP statuses on a bad key/request
# that we care about distinguishing: 403 (permission / no key) and 404 (the
# place_id is unknown or delisted). Everything else worth handling is a 429
# (quota) or a 5xx (upstream) — all of them mean "no enrichment this request".


class PlacesUnavailable(Exception):
    """Place enrichment did not happen: no key, or Google refused/failed.

    Callers treat this as "return nulls" and carry on. It is never an excuse
    to block a response.
    """


class PlacesTimeout(PlacesUnavailable):
    """Places took too long. Separate only so the caller can choose a message."""


class PlaceNotFound(PlacesUnavailable):
    """The `google_place_id` is unknown or the place was delisted."""


class PlaceForbidden(PlacesUnavailable):
    """The API key is missing, wrong, or lacks permission for Places."""


class PlacesQuota(PlacesUnavailable):
    """Daily quota exhausted. Distinct so it can re-login the caller."""


# The set of response fields we're asking for. Kept as narrow as the product
# needs so the payload stays small; `photos` is what hands us the `photo.name`
# we later proxy.
#
# Gotcha worth documenting: the Places API (New) `X-Goog-FieldMask` header takes
# the field paths *without* the leading `places.` prefix — `displayName`, not
# `places.displayName`. Sending the prefixed form returns 400
# "Cannot find matching fields for path 'places.displayName'".
FIELD_MASK = (
    "displayName,"
    "formattedAddress,"
    "rating,"
    "userRatingCount,"
    "photos,"
    "regularOpeningHours,"
    "reviews"
)


@dataclass(frozen=True)
class PlaceEnrichment:
    """Everything we keep from a Place Details response.

    Nullable fields stay null when the venue or the API doesn't provide them.
    `photo_names` are `places/…/photos/…` names from the response, which the
    proxy endpoint turns into a keyless backend URL for the client.
    """

    rating: float | None
    user_rating_count: int | None
    display_name: str | None
    formatted_address: str | None
    photo_names: list[str]
    opening_hours: list[str]
    reviews: list[dict]


def _classify_status(status_code: int, body: dict) -> PlacesUnavailable:
    """Turn an HTTP status + JSON error body into the matching exception."""
    message = body.get("message") or body.get(
        "error", {}
    ).get("message") or f"HTTP {status_code}"
    if status_code == 403:
        return PlaceForbidden(message)
    if status_code == 404:
        return PlaceNotFound(message)
    if status_code == 429:
        return PlacesQuota(message)
    return PlacesUnavailable(f"Places returned {status_code}: {message}")


def fetch_place(place_id: str) -> PlaceEnrichment:
    """One Place Details call, keyed by `google_place_id`.

    Raises `PlacesUnavailable` subclasses on any failure. The caller decides
    whether to fall back to cached data or to nulls.
    """
    if not config.PLACES_API_KEY:
        raise PlaceForbidden("GOOGLE_PLACES_API_KEY is not set")

    url = config.PLACES_DETAILS_URL.format(place_id=place_id)
    headers = {
        "X-Goog-Api-Key": config.PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
        "Content-Type": "application/json",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=config.PLACES_TIMEOUT_MS / 1000.0)
    except httpx.TimeoutException as exc:
        raise PlacesTimeout(str(exc)) from exc
    except httpx.HTTPError as exc:  # connection refused, DNS, TLS…
        raise PlacesUnavailable(str(exc)) from exc

    if response.status_code != 200:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text}
        raise _classify_status(response.status_code, body)

    place = response.json().get("place", response.json())

    photos = place.get("photos") or []
    opening_hours = (place.get("regularOpeningHours") or {}).get(
        "weekdayDescriptions", []
    )

    reviews = []
    for review in place.get("reviews") or []:
        attribution = review.get("authorAttribution") or {}
        reviews.append(
            {
                "author_name": attribution.get("displayName"),
                "rating": review.get("rating"),
                "text": review.get("text", {}).get("text") if isinstance(review.get("text"), dict) else review.get("text"),
                "relative_time": review.get("relativePublishTimeDescription"),
            }
        )

    return PlaceEnrichment(
        rating=place.get("rating"),
        user_rating_count=place.get("userRatingCount"),
        display_name=place.get("displayName", {}).get("text")
        if isinstance(place.get("displayName"), dict)
        else place.get("displayName"),
        formatted_address=place.get("formattedAddress"),
        photo_names=[photo.get("name") for photo in photos if photo.get("name")],
        opening_hours=list(opening_hours),
        reviews=reviews,
    )


# --- Caching ----------------------------------------------------------------


def is_fresh(conn: sqlite3.Connection, restaurant_id: str) -> bool:
    """True when the row's enrichment is new enough to trust as-is."""
    row = conn.execute(
        "SELECT places_synced_at FROM restaurants WHERE id = ?;",
        (restaurant_id,),
    ).fetchone()
    if row is None or not row["places_synced_at"]:
        return False
    try:
        synced = datetime.fromisoformat(row["places_synced_at"])
    except ValueError:
        return False
    return datetime.now(timezone.utc) - synced < timedelta(hours=config.PLACES_CACHE_TTL_HOURS)


def load_cached(conn: sqlite3.Connection, restaurant_id: str) -> PlaceEnrichment | None:
    """Read the cached enrichment columns back into a `PlaceEnrichment`."""
    row = conn.execute(
        "SELECT rating, user_rating_count, places_display_name, places_address, "
        "       photo_refs_json, hours_json, reviews_json "
        "FROM restaurants WHERE id = ?;",
        (restaurant_id,),
    ).fetchone()
    if row is None or row["rating"] is None and not row["photo_refs_json"]:
        return None

    def _parse_refs(raw: str | None) -> list[str]:
        try:
            return json.loads(raw) if raw else []
        except (ValueError, TypeError):
            return []

    return PlaceEnrichment(
        rating=row["rating"],
        user_rating_count=row["user_rating_count"],
        display_name=row["places_display_name"],
        formatted_address=row["places_address"],
        photo_names=_parse_refs(row["photo_refs_json"]),
        opening_hours=json.loads(row["hours_json"]) if row["hours_json"] else [],
        reviews=json.loads(row["reviews_json"]) if row["reviews_json"] else [],
    )


def save_cached(
    conn: sqlite3.Connection, restaurant_id: str, enrichment: PlaceEnrichment
) -> None:
    """Persist an enrichment into the restaurant row for reuse (DESIGN §7)."""
    conn.execute(
        """
        UPDATE restaurants SET
            rating = ?, user_rating_count = ?,
            places_display_name = ?, places_address = ?,
            photo_refs_json = ?, hours_json = ?, reviews_json = ?,
            places_synced_at = ?
        WHERE id = ?;
        """,
        (
            enrichment.rating,
            enrichment.user_rating_count,
            enrichment.display_name,
            enrichment.formatted_address,
            json.dumps(enrichment.photo_names, ensure_ascii=False),
            json.dumps(enrichment.opening_hours, ensure_ascii=False),
            json.dumps(enrichment.reviews, ensure_ascii=False),
            datetime.now(timezone.utc).isoformat(),
            restaurant_id,
        ),
    )
    conn.commit()


def enrichment_for(
    conn: sqlite3.Connection, restaurant_id: str
) -> PlaceEnrichment | None:
    """The lazy + cached accessor: reuse fresh cache, else fetch & store.

    Returns `None` (never raises) so the caller can build a detail response
    with nulls when enrichment isn't possible. A failed or slow fetch keeps
    whatever was already cached; with no cache at all it returns None and the
    caller degrades to nulls.
    """
    restaurant = conn.execute(
        "SELECT google_place_id FROM restaurants WHERE id = ?;",
        (restaurant_id,),
    ).fetchone()
    if restaurant is None or not restaurant["google_place_id"]:
        return None

    # Fresh cache wins — no network call.
    if is_fresh(conn, restaurant_id):
        cached = load_cached(conn, restaurant_id)
        if cached is not None:
            return cached

    try:
        enrichment = fetch_place(restaurant["google_place_id"])
    except PlacesUnavailable:
        # Degrade: reuse stale cache if present, else nulls.
        return load_cached(conn, restaurant_id)

    save_cached(conn, restaurant_id, enrichment)
    return enrichment


def photo_names_for(conn: sqlite3.Connection, restaurant_id: str) -> list[str]:
    """Photo `name`s for a restaurant without triggering a live fetch.

    Used by the proxy endpoint so it can serve an already-known photo without
    re-calling Details. Returns [] when none are cached.
    """
    row = conn.execute(
        "SELECT photo_refs_json FROM restaurants WHERE id = ?;",
        (restaurant_id,),
    ).fetchone()
    if row is None or not row["photo_refs_json"]:
        return []
    try:
        return json.loads(row["photo_refs_json"])
    except (ValueError, TypeError):
        return []


# --- Photo proxy ------------------------------------------------------------


def photo_urls(conn: sqlite3.Connection, restaurant_id: str) -> list[str]:
    """Keyless backend URLs for a restaurant's cached photos.

    The client can load these directly — they resolve to the proxy route on this
    server, and the real Places key is added only here, server-side (DESIGN §7).
    Photo names never leave the backend; the index is the public handle.
    """
    names = photo_names_for(conn, restaurant_id)
    return [f"/restaurants/{restaurant_id}/photos/{i}" for i in range(len(names))]


def fetch_photo_bytes(photo_name: str, max_width: int | None = None) -> bytes:
    """Fetch one Place photo's bytes *through the backend* (DESIGN §7).

    The client never holds the Places key — it asks the backend for a photo by
    its backend URL, and this does the keyed call on its behalf.
    """
    if not config.PLACES_API_KEY:
        raise PlaceForbidden("GOOGLE_PLACES_API_KEY is not set")

    url = config.PLACES_PHOTO_MEDIA_URL.format(photo_name=photo_name.lstrip("/"))
    params = {"key": config.PLACES_API_KEY}
    if max_width:
        params["maxWidthPx"] = max_width

    try:
        # The media endpoint answers with a 302 to the real image on Google's
        # content CDN — follow it, otherwise we'd proxy the redirect JSON, not
        # the photo bytes.
        response = httpx.get(
            url,
            params=params,
            timeout=config.PLACES_TIMEOUT_MS / 1000.0,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        raise PlacesTimeout(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise PlacesUnavailable(str(exc)) from exc

    if response.status_code != 200:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text}
        raise _classify_status(response.status_code, body)

    return response.content