"""Food Roulette API.

Chat, Places enrichment, and the roulette endpoint arrive in later milestones
(see ROADMAP.md §4). Everything served here matches `docs/api/openapi.yaml`.

Run from backend/:
    uvicorn app.main:app --reload --host 0.0.0.0
(`--host 0.0.0.0` so the Android emulator can reach it at 10.0.2.2:8000.)
"""
from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__, config, db, ranking, schemas
from . import filter as safety_filter  # `filter` shadows the builtin otherwise
from .llm import extract as llm_extract
from .llm import narrate as llm_narrate

# Used whenever Gemini couldn't write the reply. The cards beside it are real
# either way, so this says "here they are" rather than apologising for an outage.
DEGRADED_REPLY = "Here's what fits your saved preferences."


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
# Recommendation path. The safety rules themselves live in filter.py and the
# ordering in ranking.py — this module only moves data between them and the
# wire. Nothing here may decide whether a dish is safe.
# ---------------------------------------------------------------------------


def _ack_reason(hard: schemas.HardConstraints) -> str:
    # Shown verbatim in the confirmation dialog, so it has to name the thing the
    # user actually asked us to protect them from.
    if hard.allergens:
        return "allergen data unverified for: " + ", ".join(
            a.replace("_", " ") for a in hard.allergens
        )
    if hard.celiac:
        return "gluten data unverified for these dishes"
    if hard.jay:
        return "เจ (jay) data unverified for these dishes"
    return "dietary data unverified for these dishes"


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


def _recommend_for(
    conn,
    body: schemas.RecommendIn | schemas.ChatIn,
    hard: schemas.HardConstraints,
    soft: schemas.SoftPreferences,
) -> tuple[list[schemas.RecommendedRestaurant], bool]:
    """Filter, rank, and shape into cards. Shared by /recommend and /chat.

    Chat gets its recommendations from this same function on purpose: there is
    one safety path, and adding a conversation in front of it must not create a
    second one.
    """
    # Hard filter first, in SQL. Everything after this line is ordering.
    surviving = safety_filter.safe_dishes(conn, hard)
    restaurants = {row["id"]: dict(row) for row in conn.execute("SELECT * FROM restaurants;")}

    candidates = [
        ranking.Candidate(
            restaurant=restaurants[dishes.restaurant_id],
            dishes=dishes,
            distance_m=_distance_to(restaurants[dishes.restaurant_id], body),
        )
        for dishes in surviving
        if dishes.restaurant_id in restaurants
    ]

    ranked = ranking.rank(candidates, soft, seed=body.seed)

    # Computed over the whole safe set, not the truncated page: the banner asks
    # "did anything verified survive the filter?", which `limit` can't change.
    fallback = safety_filter.fallback_used(surviving)

    return [_to_card(c, hard) for c in ranked[: body.limit]], fallback


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
        recommendations, fallback = _recommend_for(conn, body, hard, soft)
    finally:
        conn.close()

    return schemas.RecommendOut(recommendations=recommendations, fallback_used=fallback)


@app.post("/chat", response_model=schemas.ChatOut)
def chat(body: schemas.ChatIn) -> schemas.ChatOut:
    """Read the message, filter, then describe what survived (DESIGN §6).

    Gemini sits on both ends and never in the middle: it turns the message into
    preferences, and later writes the reply, but the choice of restaurants is
    made by the same filter /recommend uses. If Gemini is unreachable the
    request still succeeds — the user gets their saved-profile recommendations
    and a `degraded` code explaining why the reply is plain.
    """
    session_id = body.session_id or uuid.uuid4().hex

    conn = db.connect()
    try:
        user = conn.execute("SELECT id FROM users WHERE id = ?;", (body.user_id,)).fetchone()
        if user is None:
            raise ApiError(404, "NOT_FOUND", "We couldn't find that account.")

        hard, soft = _load_preferences(conn, body.user_id)
        degraded: str | None = None

        try:
            extracted = llm_extract.extract(body.text)
            # Union, never replace: the message can add restrictions, not lift
            # the ones already saved.
            hard = llm_extract.union_hard_constraints(hard, extracted.hard_constraints)
            soft = llm_extract.union_soft_prefs(soft, extracted.soft_prefs)
        except llm_extract.ExtractTimeout:
            degraded = "UPSTREAM_TIMEOUT"
        except llm_extract.ExtractUnavailable:
            degraded = "LLM_UNAVAILABLE"

        recommendations, fallback = _recommend_for(conn, body, hard, soft)
        # Read while the connection is open: the grounding check below needs to
        # know which real venues we chose *not* to return.
        unreturned_names = _unreturned_restaurant_names(conn, recommendations)
    finally:
        conn.close()

    if degraded:
        # Nothing was understood from the message, so there's nothing to narrate
        # beyond the saved profile — and a second Gemini call would fail too.
        reply = DEGRADED_REPLY
    else:
        try:
            reply = llm_narrate.narrate(body.text, recommendations)
        except llm_extract.ExtractTimeout:
            reply, degraded = DEGRADED_REPLY, "UPSTREAM_TIMEOUT"
        except llm_extract.ExtractUnavailable:
            # The suggestions are still sound; only the wording was lost, and
            # the client deserves to know the prose is canned.
            reply, degraded = DEGRADED_REPLY, "LLM_UNAVAILABLE"
        else:
            if llm_narrate.ungrounded_mentions(reply, recommendations, unreturned_names):
                # The reply pointed at a restaurant that isn't in the response —
                # possibly one the safety filter threw out. Drop the prose; the
                # cards were never at risk. Reported as LLM_UNAVAILABLE because
                # from the client's side that is exactly what happened: no usable
                # reply came back, fall through to the plain results treatment.
                reply, degraded = DEGRADED_REPLY, "LLM_UNAVAILABLE"

    return schemas.ChatOut(
        reply=reply,
        recommendations=recommendations,
        session_id=session_id,
        fallback_used=fallback,
        degraded=degraded,
    )


def _unreturned_restaurant_names(
    conn, recommendations: list[schemas.RecommendedRestaurant]
) -> list[str]:
    """Real venues that aren't in this response — what a reply must not name."""
    returned = {card.restaurant_id for card in recommendations}
    return [
        row["name_th"]
        for row in conn.execute("SELECT id, name_th FROM restaurants;")
        if row["id"] not in returned and row["name_th"]
    ]


def _distance_to(restaurant: dict, body: schemas.RecommendIn | schemas.ChatIn) -> float | None:
    """None when either end lacks coordinates — the card then hides distance."""
    if body.latitude is None or body.longitude is None:
        return None
    if restaurant.get("latitude") is None or restaurant.get("longitude") is None:
        return None
    return ranking.haversine_m(
        body.latitude, body.longitude, restaurant["latitude"], restaurant["longitude"]
    )


def _to_card(
    candidate: ranking.Candidate, hard: schemas.HardConstraints
) -> schemas.RecommendedRestaurant:
    """Shape one ranked candidate into the wire object (ROADMAP §3.1)."""
    restaurant = candidate.restaurant
    dishes = candidate.dishes

    return schemas.RecommendedRestaurant(
        restaurant_id=restaurant["id"],
        name_th=restaurant.get("name_th"),
        name_en=restaurant.get("name_en"),
        latitude=restaurant.get("latitude"),
        longitude=restaurant.get("longitude"),
        distance_m=candidate.distance_m,
        price_tier=restaurant.get("price_band"),
        # rating / photo_url stay null until M4 (Places).
        rating=None,
        photo_url=None,
        safety_tier=dishes.safety_tier,
        needs_ack=dishes.needs_ack,
        ack_reason=_ack_reason(hard) if dishes.needs_ack else None,
        excluded_count=dishes.excluded_count,
        safe_dishes=[
            schemas.SafeDish(
                id=d["id"],
                name_th=d.get("name_th"),
                name_en=d.get("name_en"),
                price_thb=d.get("price_thb"),
                spicy_level=d.get("spicy_level"),
                safety_tier=safety_filter.tier_of(d),
            )
            for d in dishes.offered_dishes
        ],
    )
