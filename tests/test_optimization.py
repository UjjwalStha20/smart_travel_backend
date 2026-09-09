import pytest

from app.models import Address, Permit, RoutePoint, TrekkingRoute
from app.services.budget_optimizer import BudgetOptimizer
from app.services.route_optimizer import RouteOptimizer


# ---------------------------------------------------------------------------
# Unit tests: BudgetOptimizer
# ---------------------------------------------------------------------------

def test_budget_optimizer_feasible_plan(session, test_destinations, test_accommodation, test_food_cost):
    trek = test_destinations[0]
    session.add(Permit(destination_id=trek.id, permit_type="TIMS", category="Foreign", price=2000))
    session.commit()

    result = BudgetOptimizer(session).optimize(
        destination_id=str(trek.id),
        total_budget=50000,
        party_size=1,
        days=3,
        fee_category="Foreign",
    )

    assert result["feasible"] is True
    assert result["grand_total"] <= 50000
    assert result["minimum_budget"] > 0
    assert len(result["daily_plan"]) == 3
    assert result["one_time_fees"][0]["name"] == "TIMS"
    assert result["comfort_score"] > 0
    # A generous budget should allow upgrading to the top tier everywhere.
    assert result["daily_plan"][0]["food_tier"] == "luxury"
    assert result["daily_plan"][0]["accommodation_tier"] == "luxury"


def test_budget_optimizer_infeasible(session, test_destinations, test_accommodation, test_food_cost):
    trek = test_destinations[0]
    session.add(Permit(destination_id=trek.id, permit_type="TIMS", category="Foreign", price=2000))
    session.commit()

    result = BudgetOptimizer(session).optimize(
        destination_id=str(trek.id), total_budget=100, party_size=1, days=3
    )

    assert result["feasible"] is False
    assert result["deficit"] is not None
    assert result["deficit"] > 0
    assert result["grand_total"] > 100


def test_budget_optimizer_per_destination_estimate(session, test_destinations, test_accommodation, test_food_cost):
    """Estimate derives a destination-specific average budget from real prices."""
    trek = test_destinations[0]
    session.add(Permit(destination_id=trek.id, permit_type="TIMS", category="Foreign", price=2000))
    session.commit()

    est = BudgetOptimizer(session).estimate(str(trek.id), days=7, fee_category="Foreign")

    assert est["destination_name"] == "Annapurna Base Camp Trek"
    assert est["per_person_per_day"] > 0
    assert est["minimum_per_person_per_day"] > 0
    assert est["one_time_fees_per_person"] >= 2000
    assert est["estimated_total_per_person"] > est["per_person_per_day"] * 7
    assert est["minimum_total_per_person"] < est["estimated_total_per_person"]

    # Different duration scales the daily portion only.
    week = BudgetOptimizer(session).estimate(str(trek.id), days=7)
    two_weeks = BudgetOptimizer(session).estimate(str(trek.id), days=14)
    assert two_weeks["estimated_total_per_person"] > week["estimated_total_per_person"]


# ---------------------------------------------------------------------------
# Unit tests: RouteOptimizer
# ---------------------------------------------------------------------------

def test_route_optimizer_reorders_points_for_shorter_path(session, test_destinations):
    trek = test_destinations[0]
    route = TrekkingRoute(
        destination_id=trek.id, route_name="Test Trek",
        difficulty="moderate", recommended_days=3,
    )
    session.add(route)
    session.flush()

    coords = [
        ("Start", 28.2, 84.0),
        ("Far", 28.3, 84.3),
        ("End", 28.4, 84.0),
    ]
    addresses, points = [], []
    for i, (name, lat, lon) in enumerate(coords, start=1):
        addr = Address(province="Gandaki", district="Kaski", place=name, latitude=lat, longitude=lon, altitude=1400)
        session.add(addr)
        session.flush()
        addresses.append(addr)
        points.append(
            RoutePoint(
                route_id=route.id, sequence_no=i, name=name, address_id=addr.id,
                distance_from_previous_km=30.0, walking_hours_from_previous=6.0,
                overnight_stop=True,
            )
        )
    session.add_all(points)
    session.commit()

    result = RouteOptimizer(session).optimize(route_id=str(route.id))

    assert result["stops"] == 3
    assert result["original_order"] == ["Start", "Far", "End"]
    assert {s["name"] for s in result["optimized_order"]} == {"Start", "End", "Far"}
    assert result["savings_km"] > 0
    assert result["optimized_total_km"] < result["original_total_km"]
    assert result["savings_percent"] > 0
    assert result["total_walking_hours"] == 18.0
    # First optimized stop is the original start.
    assert result["optimized_order"][0]["name"] == "Start"


def test_route_optimizer_custom_points(session):
    result = RouteOptimizer(session).optimize(
        points=[
            {"name": "Start", "latitude": 28.2, "longitude": 84.0, "overnight": False},
            {"name": "Far", "latitude": 28.3, "longitude": 84.3, "overnight": True},
            {"name": "End", "latitude": 28.4, "longitude": 84.0, "overnight": False},
        ]
    )

    assert result["source"] == "custom"
    assert result["stops"] == 3
    assert result["optimized_order"][0]["name"] == "Start"


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_optimization_budget_endpoint(
    client, user_token, session, test_destinations, test_accommodation, test_food_cost
):
    trek = test_destinations[0]
    session.add(Permit(destination_id=trek.id, permit_type="TIMS", category="Foreign", price=2000))
    session.commit()

    response = client.post(
        "/optimization/budget",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "destination_id": str(trek.id),
            "total_budget": 50000,
            "party_size": 1,
            "days": 3,
            "fee_category": "Foreign",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is True
    assert body["destination_name"] == "Annapurna Base Camp Trek"


def test_optimization_route_endpoint(client, user_token, session, test_destinations):
    trek = test_destinations[0]
    route = TrekkingRoute(
        destination_id=trek.id, route_name="API Test Trek",
        difficulty="moderate", recommended_days=3,
    )
    session.add(route)
    session.flush()
    coords = [("Start", 28.2, 84.0), ("Far", 28.3, 84.3), ("End", 28.4, 84.0)]
    for i, (name, lat, lon) in enumerate(coords, start=1):
        addr = Address(province="Gandaki", district="Kaski", place=name, latitude=lat, longitude=lon, altitude=1400)
        session.add(addr)
        session.flush()
        session.add(RoutePoint(route_id=route.id, sequence_no=i, name=name, address_id=addr.id, overnight_stop=True))
    session.commit()

    response = client.post(
        "/optimization/route",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"route_id": str(route.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route_name"] == "API Test Trek"
    assert body["savings_km"] > 0
    assert body["optimized_order"][0]["name"] == "Start"


def test_optimization_works_without_auth(client, test_destinations):
    """Optimization endpoints are pure public computation — no login required."""
    response = client.post(
        "/optimization/budget",
        json={
            "destination_id": str(test_destinations[0].id),
            "total_budget": 5000,
            "party_size": 1,
            "days": 3,
        },
    )
    assert response.status_code == 200
    assert "destination_name" in response.json()

    response = client.post(
        "/optimization/route",
        json={
            "points": [
                {"name": "Start", "latitude": 28.2, "longitude": 84.0, "overnight": False},
                {"name": "Far", "latitude": 28.3, "longitude": 84.3, "overnight": True},
                {"name": "End", "latitude": 28.4, "longitude": 84.0, "overnight": False},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["optimized_order"][0]["name"] == "Start"


def test_destination_budget_estimate_endpoint(
    client, session, test_destinations, test_accommodation, test_food_cost
):
    trek = test_destinations[0]
    session.add(Permit(destination_id=trek.id, permit_type="TIMS", category="Foreign", price=2000))
    session.commit()

    response = client.get(f"/destinations/{trek.id}/budget-estimate?days=7&fee_category=Foreign")

    assert response.status_code == 200
    body = response.json()
    assert body["destination_name"] == "Annapurna Base Camp Trek"
    assert body["days"] == 7
    assert body["per_person_per_day"] > 0
    assert body["estimated_total_per_person"] > 0

    # Missing destination → 404.
    response = client.get("/destinations/00000000-0000-0000-0000-000000000000/budget-estimate")
    assert response.status_code == 404