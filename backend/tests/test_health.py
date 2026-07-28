"""M0 checkpoint: /health is what a new dev (and the FE team) checks first."""
from __future__ import annotations


def test_health_reports_ingested_counts(client):
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["restaurants"] == 50
    assert body["menu_items"] == 1250


def test_health_points_at_the_throwaway_db(client, test_db):
    """Proof the suite isn't quietly reading a developer's local database."""
    assert client.get("/health").json()["db"] == str(test_db["path"])


def test_restaurant_detail_includes_menu(client):
    body = client.get("/restaurants/tu_place_1").json()
    assert body["restaurant"]["id"] == "tu_place_1"
    assert len(body["menu"]) == 25
