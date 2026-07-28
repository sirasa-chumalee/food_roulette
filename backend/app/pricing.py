"""Derive each restaurant's price band from its own menu (DESIGN §7).

`restaurants.json` ships `price_band` as NULL for all 50 rows, and Google Places
(M4) may never fill it for small campus shops. Menu prices are already local, so
we compute it offline at ingest time instead of leaving the UI with a blank.

**Median, not mean** — one 999 THB seafood platter shouldn't make a noodle shop
look expensive.

Boundaries are absolute Thai baht, chosen so "$" means cheap to a student rather
than "cheapest of these 50" — a quantile split would silently re-label every
restaurant whenever the dataset changed. Over the current data they land at
15 / 19 / 12 / 4 restaurants.
"""
from __future__ import annotations

import sqlite3
import statistics

# Ordered cheapest → priciest; the index doubles as the distance metric used by
# `ranking.py` when comparing a restaurant against the user's preferred tier.
PRICE_TIERS = ("$", "$$", "$$$", "$$$$")

# Upper bound (inclusive) of the median dish price for each tier.
TIER_CEILINGS: tuple[tuple[float, str], ...] = (
    (69.0, "$"),
    (119.0, "$$"),
    (179.0, "$$$"),
)


def tier_for_median(median_price: float) -> str:
    for ceiling, tier in TIER_CEILINGS:
        if median_price <= ceiling:
            return tier
    return PRICE_TIERS[-1]


def tier_index(tier: str | None) -> int | None:
    """Position in `PRICE_TIERS`, or None for an unknown/absent band."""
    return PRICE_TIERS.index(tier) if tier in PRICE_TIERS else None


def derive_price_bands(conn: sqlite3.Connection) -> int:
    """Fill `restaurants.price_band` from each menu's median price.

    Idempotent — recomputed from scratch on every ingest. Restaurants with no
    priced dish keep a NULL band, and the client renders that as "unknown"
    rather than guessing.
    """
    rows = conn.execute(
        "SELECT restaurant_id, price_thb FROM menu_items WHERE price_thb IS NOT NULL;"
    ).fetchall()

    prices: dict[str, list[float]] = {}
    for row in rows:
        prices.setdefault(row["restaurant_id"], []).append(row["price_thb"])

    updates = [
        (tier_for_median(statistics.median(values)), restaurant_id)
        for restaurant_id, values in prices.items()
    ]
    conn.executemany("UPDATE restaurants SET price_band = ? WHERE id = ?;", updates)
    conn.commit()
    return len(updates)
