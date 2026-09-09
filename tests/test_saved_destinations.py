"""Tests for the "saved destinations" endpoints."""
from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_save_and_list_my_destinations(client: TestClient, user_token: str, test_destinations):
    """Saving a destination makes it appear in GET /saved-destinations/mine only for the owner."""
    dest_id = str(test_destinations[0].id)

    save = client.post(
        "/saved-destinations/",
        headers=_auth_headers(user_token),
        json={"destination_id": dest_id},
    )
    assert save.status_code == 201, save.text

    mine = client.get("/saved-destinations/mine", headers=_auth_headers(user_token))
    assert mine.status_code == 200, mine.text
    data = mine.json()
    assert data["total"] >= 1
    assert any(s["destination_id"] == dest_id for s in data["items"])

    unauth = client.get("/saved-destinations/mine")
    assert unauth.status_code == 401