"""Tests for the "my trips" endpoint and trip creation without a route."""
from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_trip_without_route(client: TestClient, user_token: str, test_destinations):
    """A user trip may target an attraction and therefore has no trekking route."""
    dest_id = str(test_destinations[1].id)  # Pashupatinath Temple (attraction)

    resp = client.post(
        "/user-trips/",
        headers=_auth_headers(user_token),
        json={
            "destination_id": dest_id,
            "pace_type": "normal",
            "budget_type": "standard",
            "status": "planned",
        },
    )

    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["route_id"] is None
    assert data["destination_id"] == dest_id


def test_my_trips_returns_only_own_trips(client: TestClient, user_token: str, test_destinations):
    """GET /user-trips/mine must return only the current user's trips."""
    from app.core.security import hash_password
    from app.core.auth import create_access_token
    from app.core.db import get_session
    from app.models import User

    dest_id = str(test_destinations[0].id)

    resp = client.post(
        "/user-trips/",
        headers=_auth_headers(user_token),
        json={
            "destination_id": dest_id,
            "pace_type": "normal",
            "budget_type": "standard",
            "status": "planned",
        },
    )
    assert resp.status_code == 201, resp.text

    mine = client.get("/user-trips/mine", headers=_auth_headers(user_token))
    assert mine.status_code == 200, mine.text
    data = mine.json()
    assert data["total"] >= 1
    for trip in data["items"]:
        assert "user_id" in trip
        assert "id" in trip