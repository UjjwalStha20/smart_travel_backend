"""Tests for the recommendation API endpoint."""
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
import pytest

from app.main import app
from app.core.db import engine, init_db
from app.models import User
from app.core.auth import create_access_token
from app.core.security import hash_password


# Setup test database
@pytest.fixture(autouse=True)
def setup_db():
    """Set up the database for each test."""
    init_db()
    yield


client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get an auth token for the test user."""
    # Create test user
    user = User(
        name="Test User",
        email="test@example.com",
        password=hash_password("testpass123"),
        role="traveler",
    )
    # Use a new session for user creation
    with Session(engine) as session:
        session.add(user)
        session.commit()
        # Don't call refresh - just use the user id directly
        token = create_access_token({"sub": str(user.id)})
    return f"Bearer {token}"


def test_new_user_cold_start():
    """Test that new users receive recommendations (cold start)."""
    token = auth_token()
    
    # Get recommendations for new user (no interactions) - cold start uses popularity
    recs = client.get(
        "/recommendations/",
        headers={"Authorization": token},
        params={"user_id": "test@example.com", "limit": 5}
    )
    
    # Should return recommendations (cold start uses popularity)
    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Should return at least one recommendation"
    
    # Verify response structure
    for rec in data:
        assert "destination_id" in rec, f"Missing destination_id in {rec}"
        assert "name" in rec, f"Missing name in {rec}"
        assert "category" in rec, f"Missing category in {rec}"
        assert "final_score" in rec, f"Missing final_score in {rec}"
        assert 0 <= rec["final_score"] <= 1, f"Score out of range: {rec['final_score']}"
        assert "rank" in rec, f"Missing rank in {rec}"
        assert "component_scores" in rec, f"Missing component_scores in {rec}"
        assert "explanation" in rec, f"Missing explanation in {rec}"
        
        # Check component scores structure
        comp = rec["component_scores"]
        comp_fields = ["content", "preference", "context", "collaborative", "popularity"]
        for field in comp_fields:
            assert field in comp, f"Missing component field: {field}"
            assert 0 <= comp[field] <= 1, f"Component score out of range: {field}"
        
        # Check explanation
        assert "reason_summary" in rec["explanation"], f"Missing reason_summary in {rec['explanation']}"


def test_recommendation_with_interactions():
    """Test recommendations after user interactions."""
    token = auth_token()
    
    # Get recommendations (will use existing user data)
    recs = client.get(
        "/recommendations/",
        headers={"Authorization": token},
        params={"user_id": "test@example.com", "limit": 5}
    )
    
    # Should return recommendations
    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert isinstance(data, list)


def test_recommendation_schema():
    """Test that recommendations have the expected schema."""
    token = auth_token()
    
    # Get recommendations
    recs = client.get(
        "/recommendations/",
        headers={"Authorization": token},
        params={"user_id": "test@example.com", "limit": 1}
    )
    
    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    assert len(data) > 0, "Should return at least one recommendation"
    
    rec = data[0]
    # Check all required fields are present
    required_fields = [
        "destination_id", "name", "category", "final_score",
        "component_scores", "explanation", "rank"
    ]
    for field in required_fields:
        assert field in rec, f"Missing field: {field}"
    
    # Check component scores structure
    comp = rec["component_scores"]
    comp_fields = ["content", "preference", "context", "collaborative", "popularity"]
    for field in comp_fields:
        assert field in comp, f"Missing component field: {field}"
        assert 0 <= comp[field] <= 1, f"Component score out of range: {field}"
    
    # Check explanation
    assert "reason_summary" in rec["explanation"], f"Missing reason_summary in {rec['explanation']}"


def test_recommendation_ranking():
    """Test that recommendations are properly sorted by score."""
    token = auth_token()
    
    # Get recommendations
    recs = client.get(
        "/recommendations/",
        headers={"Authorization": token},
        params={"user_id": "test@example.com", "limit": 5}
    )
    
    assert recs.status_code == 200, f"Expected 200, got {recs.status_code}: {recs.text}"
    data = recs.json()
    if len(data) > 1:
        # Verify scores are in descending order
        for i in range(len(data) - 1):
            assert data[i]["final_score"] >= data[i+1]["final_score"], \
                f"Recommendations not sorted: {data[i]['final_score']} < {data[i+1]['final_score']}"


# Run the tests
if __name__ == "__main__":
    print("Running recommendation tests...")
    
    # Run each test manually
    token = auth_token()
    
    test_new_user_cold_start()
    print("  ✓ test_new_user_cold_start passed")
    
    test_recommendation_with_interactions()
    print("  ✓ test_recommendation_with_interactions passed")
    
    test_recommendation_schema()
    print("  ✓ test_recommendation_schema passed")
    
    test_recommendation_ranking()
    print("  ✓ test_recommendation_ranking passed")
    
    print("\nAll tests passed!")
