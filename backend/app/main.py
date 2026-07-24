"""Food Roulette API — Phase 1 (minimal, runnable).

This exposes just enough to prove the data pipeline works end-to-end. The
deterministic recommendation filter, chat, and Places enrichment arrive in later
phases (see docs/DESIGN.md §10).

Run from backend/:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import __version__, config, db


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
