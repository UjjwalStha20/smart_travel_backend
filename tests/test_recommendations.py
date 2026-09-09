"""Tests for the recommendation API endpoint."""
from fastapi.testclient import TestClient
import pytest


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_new_user_with_no_signals_gets_no_recommendations(client: TestClient, user_token: str, test_destinations):
    """Cold start: users with no signals must NOT get random/popularity recommendations."""
    recs = client.get(
        "/recommendations/",
        headers=_auth_headers(user_token),
        params={"limit": 5},
    )

    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert data == [], "Expected no recommendations until the user has real signals"


def test_user_with_preferences_gets_recommendations(client: TestClient, user_token: str, test_destinations):
    """Declared preferences are a real signal and unlock recommendations."""
    resp = client.post(
        "/recommendations/preferences",
        headers=_auth_headers(user_token),
        params={
            "preferred_categories": ["trek"],
            "preferred_activities": ["hiking"],
        },
    )
    assert resp.status_code == 201, resp.text

    recs = client.get(
        "/recommendations/",
        headers=_auth_headers(user_token),
        params={"limit": 5},
    )
    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Preferences should unlock recommendations"

    for rec in data:
        assert "destination_id" in rec, f"Missing destination_id in {rec}"
        assert "name" in rec, f"Missing name in {rec}"
        assert "category" in rec, f"Missing category in {rec}"
        assert "final_score" in rec, f"Missing final_score in {rec}"
        assert 0 <= rec["final_score"] <= 1, f"Score out of range: {rec['final_score']}"
        assert "rank" in rec, f"Missing rank in {rec}"
        assert "component_scores" in rec, f"Missing component_scores in {rec}"
        assert "explanation" in rec, f"Missing explanation in {rec}"

        comp = rec["component_scores"]
        comp_fields = ["content", "preference", "context", "collaborative", "popularity"]
        for field in comp_fields:
            assert field in comp, f"Missing component field: {field}"
            assert 0 <= comp[field] <= 1, f"Component score out of range: {field}"

        assert "reason_summary" in rec["explanation"], f"Missing reason_summary in {rec['explanation']}"


def test_recommendation_with_interactions(client: TestClient, user_token: str, test_destinations):
    """Test recommendations after user interactions."""
    dest_id = str(test_destinations[0].id)

    resp = client.post(
        "/recommendations/interaction",
        headers=_auth_headers(user_token),
        params={"destination_id": dest_id, "interaction_type": "view"},
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

    recs = client.get(
        "/recommendations/",
        headers=_auth_headers(user_token),
        params={"limit": 5},
    )

    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert isinstance(data, list)


def test_recommendation_schema(client: TestClient, user_token: str, test_destinations):
    """Test that recommendations have the expected schema (user has preferences)."""
    resp = client.post(
        "/recommendations/preferences",
        headers=_auth_headers(user_token),
        params={"preferred_categories": ["trek", "attraction"]},
    )
    assert resp.status_code == 201, resp.text

    recs = client.get(
        "/recommendations/",
        headers=_auth_headers(user_token),
        params={"limit": 1},
    )

    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert len(data) > 0, "Should return at least one recommendation"

    rec = data[0]
    required_fields = [
        "destination_id", "name", "category", "final_score",
        "component_scores", "explanation", "rank",
    ]
    for field in required_fields:
        assert field in rec, f"Missing field: {field}"

    comp = rec["component_scores"]
    comp_fields = ["content", "preference", "context", "collaborative", "popularity"]
    for field in comp_fields:
        assert field in comp, f"Missing component field: {field}"
        assert 0 <= comp[field] <= 1, f"Component score out of range: {field}"

    assert "reason_summary" in rec["explanation"], f"Missing reason_summary in {rec['explanation']}"


def test_recommendation_ranking(client: TestClient, user_token: str, test_destinations):
    """Test that recommendations are properly sorted by score."""
    resp = client.post(
        "/recommendations/preferences",
        headers=_auth_headers(user_token),
        params={"preferred_categories": ["trek", "attraction"]},
    )
    assert resp.status_code == 201, resp.text

    recs = client.get(
        "/recommendations/",
        headers=_auth_headers(user_token),
        params={"limit": 5},
    )

    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    if len(data) > 1:
        for i in range(len(data) - 1):
            assert data[i]["final_score"] >= data[i + 1]["final_score"], \
                f"Recommendations not sorted: {data[i]['final_score']} < {data[i + 1]['final_score']}"


def test_preferences_defaults_and_round_trip(client: TestClient, user_token: str):
    """GET /recommendations/preferences returns defaults, POST persists them."""
    first = client.get("/recommendations/preferences", headers=_auth_headers(user_token))
    assert first.status_code == 200, first.text
    first_data = first.json()
    assert first_data["preferred_categories"] == []
    assert first_data["budget_preference"] is None

    resp = client.post(
        "/recommendations/preferences",
        headers=_auth_headers(user_token),
        params={
            "preferred_categories": ["trek", "attraction"],
            "preferred_activities": ["hiking", "cultural"],
            "budget_preference": "standard",
            "typical_duration": 8,
            "difficulty_preference": "moderate",
            "preferred_season": ["spring", "autumn"],
            "travel_style": "adventure",
        },
    )
    assert resp.status_code == 201, resp.text

    second = client.get("/recommendations/preferences", headers=_auth_headers(user_token))
    assert second.status_code == 200, second.text
    data = second.json()
    assert data["preferred_categories"] == ["trek", "attraction"]
    assert data["preferred_activities"] == ["hiking", "cultural"]
    assert data["budget_preference"] == "standard"
    assert data["typical_duration"] == 8
    assert data["difficulty_preference"] == "moderate"
    assert data["preferred_season"] == ["spring", "autumn"]
    assert data["travel_style"] == "adventure"