"""Tests for the Plan-a-Trip requirements recommendation endpoint."""

from fastapi.testclient import TestClient

from app.chat.intent import RECOMMENDATION
from app.chat.recommender import build_requirements


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_build_requirements_season_override():
    """An explicit season should win over (empty) message-derived season."""
    req = build_requirements(RECOMMENDATION, "hello", None, season="autumn")
    assert req["season"] == "autumn"
    assert req["user_profile"]["preferred_season"] == ["autumn"]

    # Without an override the message is still the source of truth.
    default = build_requirements(RECOMMENDATION, "plan a trip in October", None)
    assert default["season"] == "autumn"


def test_requirements_endpoint_returns_ranked_recommendations(
    client: TestClient, user_token: str, test_destinations
):
    """Trek trip requirements should surface trek destinations with reasons."""
    resp = client.post(
        "/recommendations/from-requirements",
        headers=_auth_headers(user_token),
        json={
            "trip_types": ["trekking"],
            "preferences": {"interests": ["sunrise", "annapurna"]},
            "answers": {"difficulty": "moderate"},
            "duration_days": 7,
            "budget_level": "moderate",
            "season": "autumn",
            "start_date": "2026-10-12",
            "limit": 5,
        },
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Should return at least one recommendation"

    for rec in data:
        assert "destination_id" in rec
        assert "name" in rec
        assert "category" in rec
        assert "score" in rec
        assert 0 <= rec["score"] <= 100, f"Score out of range: {rec['score']}"
        assert "reason" in rec and rec["reason"], "Reason should be present"

    # Ranked by score descending.
    scores = [r["score"] for r in data]
    assert scores == sorted(scores, reverse=True)

    # Trek journey should rank a trek destination first.
    assert data[0]["category"] == "trek"


def test_requirements_endpoint_falls_back_to_start_month(
    client: TestClient, user_token: str, test_destinations
):
    """Season should be derived from start_date month when not supplied."""
    resp = client.post(
        "/recommendations/from-requirements",
        headers=_auth_headers(user_token),
        json={"trip_types": ["cultural & heritage"], "start_date": "2026-10-01", "limit": 3},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) > 0


def test_requirements_endpoint_empty_ok(client: TestClient, user_token: str, test_destinations):
    """An empty body still returns a ranked list (all-optional contract)."""
    resp = client.post(
        "/recommendations/from-requirements",
        headers=_auth_headers(user_token),
        json={},
    )
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)