"""The deterministic hard-constraint filter (DESIGN §4).

This is the medical-safety path. Two rules govern everything in this module:

1.  **No LLM, no scoring, no heuristics.** A dish either satisfies every hard
    constraint or it is gone. Nothing downstream — ranking, Gemini, the roulette
    — is ever shown a dish this file rejected.
2.  **Unknown counts as unsafe.** A NULL flag is treated as if the allergen were
    present (`COALESCE(col, 1)`). Missing data must never pass a hard filter.

The filter is expressed as a SQL `WHERE` fragment rather than a Python loop so
that exclusion happens in the database, before rows are ever materialised — you
cannot forget to apply it to a list you already hold.

    where, params = filter.build_where(hard)
    conn.execute(f"SELECT * FROM menu_items WHERE {where};", params)
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .schemas import HardConstraints

# --- Tiers (DESIGN §4) -------------------------------------------------------
# A dish that survives the filter is still labelled by how much we trust the
# data behind it. Tier B is shown with a caution badge, never silently dropped.
TIER_VERIFIED = "verified"
TIER_UNVERIFIED = "unverified"

# "Shellfish" is not one column in this dataset — it's crustaceans OR molluscs.
# One user-facing allergen can therefore mean excluding on several columns.
ALLERGEN_COLUMNS: dict[str, tuple[str, ...]] = {
    "peanuts": ("peanuts",),
    "tree_nuts": ("tree_nuts",),
    "shellfish": ("crustaceans", "molluscs"),
    "fish": ("fish",),
    "wheat": ("wheat",),
    "soy": ("soy",),
    "milk": ("milk",),
    "eggs": ("eggs",),
    "sesame": ("sesame",),
}


def _absent(column: str) -> str:
    """`column` is known to be 0. NULL (unknown) fails this on purpose."""
    return f"COALESCE({column}, 1) = 0"


def _present(column: str) -> str:
    """`column` is known to be 1. NULL (unknown) fails this on purpose."""
    return f"COALESCE({column}, 0) = 1"


def build_where(hard: HardConstraints) -> tuple[str, tuple]:
    """Compile hard constraints into a `WHERE` fragment over `menu_items`.

    Returns `(sql, params)`. The fragment is always a complete, parenthesised
    boolean expression — safe to `AND` into a larger query — and is `"1 = 1"`
    when the user has no hard constraints at all.

    No user input reaches the SQL string: allergen names are looked up in
    `ALLERGEN_COLUMNS` (pydantic has already restricted them to that set), and
    every clause is built from column-name constants.
    """
    clauses: list[str] = []

    for allergen in hard.allergens:
        # Unknown allergens can't reach here — `schemas.Allergen` is a Literal —
        # but fail loudly rather than silently skipping a medical constraint.
        columns = ALLERGEN_COLUMNS[allergen]
        clauses.append(" AND ".join(_absent(col) for col in columns))

    if hard.halal:
        # The dataset's `is_halal_certified` is a placeholder 0 on all 50 rows,
        # so filtering on it would exclude everything. Derive from the dish
        # flags instead (DESIGN §4, ROADMAP §6).
        clauses.append(_absent("contains_pork"))
        clauses.append(_absent("contains_alcohol"))

    if hard.no_beef:
        clauses.append(_absent("contains_beef"))

    # Independent, not elif: a profile carrying both must satisfy both, even if
    # the source data ever disagrees with itself about vegan implying vegetarian.
    if hard.vegetarian:
        clauses.append(_present("is_vegetarian"))

    if hard.vegan:
        clauses.append(_present("is_vegan"))

    if hard.jain:
        # Jainism: vegetarian (dairy allowed) and no root/pungent vegetables.
        clauses.append(_present("is_vegetarian"))
        clauses.append(_absent("contains_pungent_veg"))

    if hard.jay:
        # Thai เจ is stricter than Jain — vegan *and* no pungent veg. The data
        # carries it pre-derived, and it agrees exactly with
        # `is_vegan AND NOT contains_pungent_veg` across all 1250 rows.
        clauses.append(_present("is_jay"))

    if hard.celiac:
        clauses.append(_absent("wheat"))

    if not clauses:
        return "1 = 1", ()

    return " AND ".join(f"({clause})" for clause in clauses), ()


def tier_of(dish: dict | sqlite3.Row) -> str:
    """Tier A (`verified`) only for `confidence='high'` — anything else is B."""
    return TIER_VERIFIED if dish["confidence"] == "high" else TIER_UNVERIFIED


@dataclass(frozen=True)
class RestaurantDishes:
    """One restaurant's survivors, already split by tier.

    `total_dishes` is the size of the menu *before* filtering, so the UI can
    honestly say "we filtered out N dishes".
    """

    restaurant_id: str
    verified: list[dict]
    unverified: list[dict]
    total_dishes: int

    @property
    def survivors(self) -> list[dict]:
        return self.verified + self.unverified

    @property
    def excluded_count(self) -> int:
        return self.total_dishes - len(self.survivors)

    @property
    def safety_tier(self) -> str:
        """A restaurant is only Tier A if it has at least one Tier-A dish."""
        return TIER_VERIFIED if self.verified else TIER_UNVERIFIED

    @property
    def offered_dishes(self) -> list[dict]:
        """What the card shows.

        Tier-A dishes when any exist; otherwise the Tier-B fallback, so a
        restaurant with something safe is never returned empty-handed
        (DESIGN §4, "never empty-handed").
        """
        return self.verified or self.unverified

    @property
    def needs_ack(self) -> bool:
        """Tier-B cards must be acknowledged before the user can act on them."""
        return not self.verified


def safe_dishes(conn: sqlite3.Connection, hard: HardConstraints) -> list[RestaurantDishes]:
    """Every restaurant with ≥1 dish that survives `hard`, tiered.

    Restaurants with no surviving dish are not recommendable and are simply
    absent from the result (DESIGN §4, "restaurant viability").
    """
    where, params = build_where(hard)

    survivors: dict[str, list[dict]] = {}
    for row in conn.execute(
        f"SELECT * FROM menu_items WHERE {where} ORDER BY restaurant_id, id;", params
    ):
        survivors.setdefault(row["restaurant_id"], []).append(dict(row))

    # Menu sizes come from a separate, unfiltered count — deriving them from the
    # filtered rows would make `excluded_count` structurally unable to be wrong.
    totals = {
        row["restaurant_id"]: row["n"]
        for row in conn.execute(
            "SELECT restaurant_id, COUNT(*) AS n FROM menu_items GROUP BY restaurant_id;"
        )
    }

    return [
        RestaurantDishes(
            restaurant_id=restaurant_id,
            verified=[d for d in dishes if tier_of(d) == TIER_VERIFIED],
            unverified=[d for d in dishes if tier_of(d) == TIER_UNVERIFIED],
            total_dishes=totals.get(restaurant_id, len(dishes)),
        )
        for restaurant_id, dishes in survivors.items()
    ]


def fallback_used(results: list[RestaurantDishes]) -> bool:
    """True when we found something, but nothing verified.

    The client shows the "no verified-safe options found" banner in this state
    — a distinct, more cautious message than an empty result.
    """
    return bool(results) and all(r.safety_tier == TIER_UNVERIFIED for r in results)
