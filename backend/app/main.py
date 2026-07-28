"""Food Roulette API.

Chat, Places enrichment, and the roulette endpoint arrive in later milestones
(see ROADMAP.md §4). Everything served here matches `docs/api/openapi.yaml`.

Run from backend/:
    uvicorn app.main:app --reload --host 0.0.0.0
(`--host 0.0.0.0` so the Android emulator can reach it at 10.0.2.2:8000.)
"""
from __future__ import annotations

import json
import math
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    # Nothing is cookie-authenticated (the mock session hands back a bearer
    # token), so credentials stay off — that's what lets "*" be legal here.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error envelope (ROADMAP §3.2). Every non-2xx leaves through one of these, so
# the client only ever has to parse one error shape.
# ---------------------------------------------------------------------------


def error_response(status_code: int, code: str, message: str, detail: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "detail": detail}},
    )


class ApiError(HTTPException):
    """Raise this instead of HTTPException to pick the envelope's `code`."""

    def __init__(self, status_code: int, code: str, message: str, detail: str | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.log_detail = detail


@app.exception_handler(ApiError)
async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.log_detail)


@app.exception_handler(StarletteHTTPException)
async def _http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Anything raised as a plain HTTPException still comes out in the envelope —
    # including the router's own 404 for an unknown path, which is a *Starlette*
    # HTTPException, not FastAPI's subclass.
    code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL"
    return error_response(exc.status_code, code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        422,
        "INVALID_PREFS",
        "Some of the values sent aren't valid.",
        # The full pydantic report is useful in a log, not on a user's screen.
        detail=str(exc.errors()),
    )


@app.exception_handler(Exception)
async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak a stack trace into `message` — ROADMAP §3.2.
    return error_response(500, "INTERNAL", "Something went wrong on our side.")


def custom_openapi() -> dict:
    """FastAPI's generated spec, plus the error envelope it can't infer.

    The envelope is produced by exception handlers rather than by a route's
    `response_model`, so it has to be declared here or `docs/api/openapi.yaml`
    would promise the frontend an error shape we don't actually send.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=(
            "Contract for the Flutter client. Frozen per ROADMAP §3 — additive "
            "changes are safe, renames are not.\n\n"
            "Every non-2xx response uses the ErrorEnvelope shape."
        ),
        routes=app.routes,
    )

    schema.setdefault("components", {}).setdefault("schemas", {}).update(
        {
            "ErrorBody": schemas.ErrorBody.model_json_schema(),
            "ErrorEnvelope": schemas.ErrorEnvelope.model_json_schema(
                ref_template="#/components/schemas/{model}"
            ),
        }
    )

    error_ref = {
        "description": "Error envelope (ROADMAP §3.2)",
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/ErrorEnvelope"}}
        },
    }
    for path in schema["paths"].values():
        for operation in path.values():
            operation.setdefault("responses", {})
            # FastAPI auto-documents a 422 in its own shape; ours is the envelope.
            operation["responses"]["422"] = error_ref
            operation["responses"]["default"] = error_ref

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


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
            raise ApiError(404, "NOT_FOUND", "We couldn't find that restaurant.")
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


def _ack_reason(hard: schemas.HardConstraints) -> str:
    # Shown verbatim in the confirmation dialog, so it has to name the thing the
    # user actually asked us to protect them from.
    if hard.allergens:
        return "allergen data unverified for: " + ", ".join(
            a.replace("_", " ") for a in hard.allergens
        )
    if hard.celiac:
        return "gluten data unverified for these dishes"
    return "dietary data unverified for these dishes"


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
            raise ApiError(404, "NOT_FOUND", "We couldn't find that account.")
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
            raise ApiError(404, "NOT_FOUND", "We couldn't find that account.")
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
            raise ApiError(404, "NOT_FOUND", "We couldn't find that account.")
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
            latitude=c["restaurant"].get("latitude"),
            longitude=c["restaurant"].get("longitude"),
            distance_m=c["distance_m"],
            price_tier=c["restaurant"].get("price_band"),
            # rating / photo_url stay null until M4 (Places).
            rating=None,
            photo_url=None,
            safety_tier=c["safety_tier"],
            needs_ack=c["needs_ack"],
            ack_reason=_ack_reason(hard) if c["needs_ack"] else None,
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
