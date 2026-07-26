"""Food Roulette API — Phase 1 (minimal, runnable).

This exposes just enough to prove the data pipeline works end-to-end. The
deterministic recommendation filter, chat, and Places enrichment arrive in later
phases (see docs/DESIGN.md §10).

Run from backend/:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

import json
import math
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from . import __version__, config, db, schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist so a fresh clone that ran ingest (or not) still boots.
    conn = db.connect()
    try:
        db.init_schema(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Food Roulette API", version=__version__, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """Liveness + a quick row count so you can confirm ingest ran."""
    conn = db.connect()
    try:
        restaurants = conn.execute("SELECT COUNT(*) FROM restaurants;").fetchone()[0]
        menu_items = conn.execute("SELECT COUNT(*) FROM menu_items;").fetchone()[0]
    finally:
        conn.close()
    return {
        "status": "ok",
        "version": __version__,
        "db": str(config.DB_PATH),
        "restaurants": restaurants,
        "menu_items": menu_items,
    }


@app.get("/restaurants")
def list_restaurants() -> list[dict]:
    """All restaurants with a count of their menu items (smoke-test endpoint)."""
    conn = db.connect()
    try:
        rows = conn.execute(
            "SELECT r.id, r.name_th, r.latitude, r.longitude, "
            "       COUNT(m.id) AS menu_count "
            "FROM restaurants r "
            "LEFT JOIN menu_items m ON m.restaurant_id = r.id "
            "GROUP BY r.id "
            "ORDER BY r.id;"
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: str) -> dict:
    """A restaurant plus its full menu (used to eyeball the ingested data)."""
    conn = db.connect()
    try:
        restaurant = conn.execute(
            "SELECT * FROM restaurants WHERE id = ?;", (restaurant_id,)
        ).fetchone()
        if restaurant is None:
            raise HTTPException(status_code=404, detail="restaurant not found")
        menu = conn.execute(
            "SELECT * FROM menu_items WHERE restaurant_id = ? ORDER BY id;",
            (restaurant_id,),
        ).fetchall()
    finally:
        conn.close()
    return {"restaurant": dict(restaurant), "menu": [dict(m) for m in menu]}


# ---------------------------------------------------------------------------
# Safety filter: plain Python rules, no AI involved. A dish either follows
# every rule or it gets dropped. No exceptions, no guessing.
# ---------------------------------------------------------------------------

# "Shellfish" isn't one thing in the data — it's two columns, crustaceans and
# molluscs. So one allergen here can mean checking two boxes, not one.
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


def _flag(dish: dict, col: str) -> bool:
    # Some columns store True/False, others store 1/0. `== 1` treats both the
    # same way, so this works no matter which one we're reading.
    return dish.get(col) == 1


def _dish_survives(dish: dict, hard: schemas.HardConstraints) -> bool:
    for allergen in hard.allergens:
        if any(_flag(dish, col) for col in ALLERGEN_COLUMNS[allergen]):
            return False

    if hard.halal and (_flag(dish, "contains_pork") or _flag(dish, "contains_alcohol")):
        # There's no real "halal" switch in the data yet. So we fake one the
        # simple way: no pork, no alcohol. Close enough for now.
        return False

    if hard.no_beef and _flag(dish, "contains_beef"):
        return False

    if hard.vegan and not _flag(dish, "is_vegan"):
        return False
    elif hard.vegetarian and not _flag(dish, "is_vegetarian"):
        return False

    if hard.jain and (not _flag(dish, "is_vegetarian") or _flag(dish, "contains_pungent_veg")):
        return False

    if hard.celiac and _flag(dish, "wheat"):
        return False

    return True


def _dish_tier(dish: dict) -> str:
    # "verified" = we trust this dish's allergy info. "unverified" = it passed
    # the filter but the data behind it is shaky, so we still show the dish —
    # just with a warning label instead of hiding it.
    return "verified" if dish.get("confidence") == "high" else "unverified"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _load_preferences(conn, user_id: str) -> tuple[schemas.HardConstraints, schemas.SoftPreferences]:
    row = conn.execute(
        "SELECT hard_json, soft_json FROM user_preferences WHERE user_id = ?;", (user_id,)
    ).fetchone()
    hard = schemas.HardConstraints(**json.loads(row["hard_json"])) if row and row["hard_json"] else schemas.HardConstraints()
    soft = schemas.SoftPreferences(**json.loads(row["soft_json"])) if row and row["soft_json"] else schemas.SoftPreferences()
    return hard, soft


@app.post("/auth/session", response_model=schemas.SessionOut, status_code=201)
def create_session(body: schemas.SessionIn) -> schemas.SessionOut:
    """Fake login for now. Hands out an ID and a token, but nothing checks the
    token yet — real login comes later."""
    conn = db.connect()
    try:
        user_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO users (id, display_name, created_at) VALUES (?, ?, ?);",
            (user_id, body.display_name, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return schemas.SessionOut(user_id=user_id, token=token, display_name=body.display_name)


@app.get("/users/{user_id}/preferences", response_model=schemas.PreferencesOut)
def get_preferences(user_id: str) -> schemas.PreferencesOut:
    """Look up a user's saved allergy/diet settings. If they've never saved any,
    hand back empty defaults instead of an error."""
    conn = db.connect()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?;", (user_id,)).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        hard, soft = _load_preferences(conn, user_id)
    finally:
        conn.close()
    return schemas.PreferencesOut(user_id=user_id, hard=hard, soft=soft)


@app.put("/users/{user_id}/preferences", response_model=schemas.PreferencesOut)
def put_preferences(user_id: str, body: schemas.PreferencesIn) -> schemas.PreferencesOut:
    """Save (or overwrite) a user's allergy/diet settings."""
    conn = db.connect()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?;", (user_id,)).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, hard_json, soft_json) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET hard_json = excluded.hard_json, soft_json = excluded.soft_json;
            """,
            (user_id, body.hard.model_dump_json(), body.soft.model_dump_json()),
        )
        conn.commit()
    finally:
        conn.close()
    return schemas.PreferencesOut(user_id=user_id, hard=body.hard, soft=body.soft)


@app.post("/recommend", response_model=schemas.RecommendOut)
def recommend(body: schemas.RecommendIn) -> schemas.RecommendOut:
    """Pick restaurants for this user. First we throw out every dish that
    breaks a hard rule (allergy, halal, etc.) — no exceptions. Then, among
    what's left, we sort by how well it matches soft preferences like spice
    level and distance."""
    conn = db.connect()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?;", (body.user_id,)).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        hard, soft = _load_preferences(conn, body.user_id)

        restaurants = [dict(r) for r in conn.execute("SELECT * FROM restaurants;").fetchall()]
        menu_items = [dict(m) for m in conn.execute("SELECT * FROM menu_items;").fetchall()]
    finally:
        conn.close()

    dishes_by_restaurant: dict[str, list[dict]] = {}
    for dish in menu_items:
        dishes_by_restaurant.setdefault(dish["restaurant_id"], []).append(dish)

    candidates = []
    for restaurant in restaurants:
        dishes = dishes_by_restaurant.get(restaurant["id"], [])
        survivors = [d for d in dishes if _dish_survives(d, hard)]
        if not survivors:
            continue  # no safe dish here at all, so skip this restaurant

        verified = [d for d in survivors if _dish_tier(d) == "verified"]
        unverified = [d for d in survivors if _dish_tier(d) == "unverified"]

        if verified:
            safe_dishes, safety_tier, needs_ack = verified, "verified", False
        else:
            # Nothing verified made it through, but something unverified did.
            # Show it anyway instead of an empty list — just make the app ask
            # "are you sure?" before the user picks it.
            safe_dishes, safety_tier, needs_ack = unverified, "unverified", True

        distance_m = None
        if body.latitude is not None and body.longitude is not None and restaurant.get("latitude") is not None:
            distance_m = _haversine_m(body.latitude, body.longitude, restaurant["latitude"], restaurant["longitude"])

        score = 0.0
        if soft.spicy_tolerance is not None:
            avg_spice = sum(d.get("spicy_level") or 0 for d in safe_dishes) / len(safe_dishes)
            score -= abs(avg_spice - soft.spicy_tolerance)
        if distance_m is not None:
            score -= distance_m / 1000.0
        if safety_tier == "verified":
            score += 10.0  # trusted restaurants jump ahead of "please confirm" ones

        candidates.append(
            {
                "restaurant": restaurant,
                "safe_dishes": safe_dishes,
                "safety_tier": safety_tier,
                "needs_ack": needs_ack,
                "excluded_count": len(dishes) - len(survivors),
                "distance_m": distance_m,
                "score": score,
            }
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)
    top = candidates[: body.limit]

    # True only if EVERY restaurant we're returning is unverified — that's the
    # signal for the app to show a "please double-check these" banner.
    fallback_used = bool(top) and all(c["safety_tier"] == "unverified" for c in top)

    recommendations = [
        schemas.RecommendedRestaurant(
            restaurant_id=c["restaurant"]["id"],
            name_th=c["restaurant"].get("name_th"),
            name_en=c["restaurant"].get("name_en"),
            distance_m=c["distance_m"],
            price_tier=c["restaurant"].get("price_band"),
            safety_tier=c["safety_tier"],
            needs_ack=c["needs_ack"],
            excluded_count=c["excluded_count"],
            safe_dishes=[
                schemas.SafeDish(
                    id=d["id"],
                    name_th=d.get("name_th"),
                    name_en=d.get("name_en"),
                    price_thb=d.get("price_thb"),
                    spicy_level=d.get("spicy_level"),
                    safety_tier=_dish_tier(d),
                )
                for d in c["safe_dishes"]
            ],
        )
        for c in top
    ]

    return schemas.RecommendOut(recommendations=recommendations, fallback_used=fallback_used)
