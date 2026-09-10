"""Tests for the Trip Plan domain (structured planning + initial itinerary + trip chat)."""
import types

import pytest
from fastapi.testclient import TestClient


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_trip(client: TestClient, token: str, **overrides):
    payload = {
        "name": "Pokhara Adventure",
        "destinations": ["Pashupatinath Temple"],
        "start_location": "Kathmandu",
        "duration_days": 3,
        "travelers": {"count": 2, "type": "couple"},
        "budget": {"amount": 30000, "currency": "NPR", "level": "moderate"},
        "trip_types": ["cultural", "mountain"],
        "transportation": ["private"],
        "accommodation": "mid-range",
        "preferences": {"pace": "normal", "interests": ["heritage"]},
        **overrides,
    }
    resp = client.post("/trip-plans/", json=payload, headers=_auth(token))
    assert resp.status_code == 201, f"create failed: {resp.status_code} {resp.text}"
    return resp.json()


def test_create_and_get_trip_plan(client: TestClient, user_token: str):
    data = _create_trip(client, user_token)
    assert data["id"]
    assert data["name"] == "Pokhara Adventure"
    assert data["status"] == "draft"
    assert data["destinations"] == ["Pashupatinath Temple"]
    assert data["budget"]["level"] == "moderate"
    assert data["itinerary_days"] == []

    trip_id = data["id"]
    resp = client.get(f"/trip-plans/{trip_id}", headers=_auth(user_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == trip_id


def test_generate_initial_itinerary(client: TestClient, user_token: str, test_destinations):
    data = _create_trip(client, user_token, duration_days=3)
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "generated"
    days = body["trip"]["itinerary_days"]
    assert len(days) >= 1, "expected at least one itinerary day"
    first = days[0]
    assert first["day_number"] == 1
    assert first["items"], "day should include at least one item"
    assert first["items"][0]["title"]


def test_preview_endpoint_works_without_auth(client: TestClient, test_destinations, session):
    from app.models import Destination, DestinationThingToDo

    pat = test_destinations[1]
    session.add_all([
        DestinationThingToDo(destination_id=pat.id, position=0, title="Visit the main temple", duration="1-2 hours"),
        DestinationThingToDo(destination_id=pat.id, position=1, title="Watch the evening aarti", duration="1 hour"),
    ])
    session.commit()

    resp = client.post("/trip-plans/preview", json={
        "destinations": ["Pashupatinath Temple"],
        "duration_days": 3,
        "transportation": ["private"],
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "preview"
    days = body["days"]
    assert len(days) == 1, "a single sightseeing destination must get exactly one preview day"
    assert days[0]["day_number"] == 1
    titles = [it["title"] for it in days[0]["items"]]
    assert "Visit the main temple" in titles
    assert days[0]["transportation"] == ["private"]


def test_preview_for_trek_uses_route_rows(client: TestClient, test_destinations, session):
    from app.models import DestinationItinerary

    abc = test_destinations[0]
    session.add_all([
        DestinationItinerary(
            destination_id=abc.id, day_number=1, title="Kathmandu to Pokhara",
            start_location="Kathmandu", end_location="Pokhara", overnight_location="Pokhara",
        ),
        DestinationItinerary(
            destination_id=abc.id, day_number=2, title="Pokhara to Ghandruk",
            start_location="Pokhara", end_location="Ghandruk", overnight_location="Ghandruk",
        ),
    ])
    session.commit()

    resp = client.post("/trip-plans/preview", json={
        "destinations": ["Annapurna Base Camp Trek"],
        "duration_days": 4,
    })
    assert resp.status_code == 200, resp.text
    days = resp.json()["days"]
    assert len(days) == 2, "preview should walk only the real route rows for a trek"
    assert "Kathmandu" in days[0]["items"][0]["title"], "trek preview should include the travel leg"


def test_trek_itinerary_uses_route_rows(client: TestClient, user_token: str, test_destinations, session):
    from app.models import DestinationItinerary

    abc = test_destinations[0]
    session.add_all([
        DestinationItinerary(
            destination_id=abc.id, day_number=1, title="Kathmandu to Pokhara",
            start_location="Kathmandu", end_location="Pokhara", overnight_location="Pokhara",
        ),
        DestinationItinerary(
            destination_id=abc.id, day_number=2, title="Pokhara to Ghandruk",
            start_location="Pokhara", end_location="Ghandruk", overnight_location="Ghandruk",
        ),
        DestinationItinerary(
            destination_id=abc.id, day_number=3, title="Ghandruk to Tolka",
            start_location="Ghandruk", end_location="Tolka", overnight_location="Tolka",
        ),
    ])
    session.commit()

    data = _create_trip(
        client, user_token,
        name="ABC Trek", destinations=["Annapurna Base Camp Trek"],
        duration_days=3, trip_types=["trekking", "mountain"],
    )
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    assert resp.status_code == 200, resp.text
    days = resp.json()["trip"]["itinerary_days"]
    assert [d["title"] for d in days] == ["Kathmandu to Pokhara", "Pokhara to Ghandruk", "Ghandruk to Tolka"]
    assert len(days) == 3
    assert any(it["category"] == "travel" for it in days[0]["items"])
    assert all(not ("— Day" in d["title"]) for d in days)


def test_trek_itinerary_caps_at_duration(client: TestClient, user_token: str, test_destinations, session):
    from app.models import DestinationItinerary

    abc = test_destinations[0]
    session.add_all([
        DestinationItinerary(
            destination_id=abc.id, day_number=n, title=f"Stage {n}",
            start_location=f"S{n}", end_location=f"E{n}",
        )
        for n in range(1, 5)
    ])
    session.commit()

    data = _create_trip(client, user_token, name="Short ABC", destinations=["Annapurna Base Camp Trek"], duration_days=2, trip_types=["trekking"])
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    days = resp.json()["trip"]["itinerary_days"]
    assert [d["title"] for d in days] == ["Stage 1", "Stage 2"]


def test_sightseeing_destination_not_repeated_across_days(client: TestClient, user_token: str, test_destinations, session):
    from app.models import DestinationThingToDo

    pat = test_destinations[1]
    session.add_all([
        DestinationThingToDo(destination_id=pat.id, position=0, title="Visit the main temple", duration="1-2 hours"),
        DestinationThingToDo(destination_id=pat.id, position=1, title="Watch the evening aarti", duration="1 hour"),
    ])
    session.commit()

    data = _create_trip(client, user_token, name="Kathmandu", destinations=["Pashupatinath Temple"], duration_days=5, trip_types=["cultural"])
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    days = resp.json()["trip"]["itinerary_days"]
    assert len(days) == 1, "a single sightseeing destination must get exactly one day"
    assert days[0]["title"] == "Pashupatinath Temple"
    titles = [it["title"] for it in days[0]["items"]]
    assert "Visit the main temple" in titles
    assert "Watch the evening aarti" in titles
    assert not any("— Day" in d["title"] for d in days)


def test_sightseeing_grouped_when_days_short(client: TestClient, user_token: str, test_destinations, test_addresses, session):
    from app.models import Destination, DestinationCategory, DestinationThingToDo

    buddha = Destination(
        name="Boudhanath Stupa", category=DestinationCategory.attraction,
        description="Buddhist stupa in Kathmandu.", best_time=[], permit_required=False,
        rating=4, address_id=test_addresses[0].id,
    )
    session.add(buddha)
    session.flush()
    session.add_all([
        DestinationThingToDo(destination_id=buddha.id, position=0, title="Circumambulate the stupa", duration="1 hour"),
    ])
    session.commit()

    data = _create_trip(
        client, user_token, name="Kathmandu Darshan",
        destinations=["Pashupatinath Temple", "Boudhanath Stupa"],
        duration_days=1, trip_types=["cultural"],
    )
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    days = resp.json()["trip"]["itinerary_days"]
    assert len(days) == 1
    assert days[0]["title"] == "Pashupatinath Temple & Boudhanath Stupa"


def test_route_trip_keeps_selected_sightseeing(client: TestClient, user_token: str, test_destinations, test_addresses, session):
    from app.models import Destination, DestinationCategory, DestinationItinerary, DestinationThingToDo

    abc = test_destinations[0]
    session.add_all([
        DestinationItinerary(
            destination_id=abc.id, day_number=n, title=f"Stage {n}",
            start_location=f"S{n}", end_location=f"E{n}",
        )
        for n in range(1, 4)
    ])
    pat = test_destinations[1]
    session.add(DestinationThingToDo(destination_id=pat.id, position=0, title="Visit the main temple"))
    session.flush()
    session.commit()

    data = _create_trip(
        client, user_token, name="Trek plus culture",
        destinations=["Annapurna Base Camp Trek", "Pashupatinath Temple"],
        duration_days=3, trip_types=["trekking"],
    )
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    days = resp.json()["trip"]["itinerary_days"]
    assert len(days) == 3
    assert [d["title"] for d in days] == ["Stage 1", "Stage 2", "Stage 3"]
    assert any(it["title"] == "Visit the main temple" for d in days for it in d["items"]), \
        "selected sightseeing destination must not be silently dropped"


def test_list_trip_plans_returns_pagination(client: TestClient, user_token: str):
    _create_trip(client, user_token)
    _create_trip(client, user_token, name="Second Trip")
    resp = client.get("/trip-plans/?offset=0&limit=10", headers=_auth(user_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["offset"] == 0
    assert body["limit"] == 10
    assert len(body["items"]) == 2
    assert {t["name"] for t in body["items"]} == {"Pokhara Adventure", "Second Trip"}


def test_ownership_enforced(client: TestClient, session, user_token, admin_token):
    from app.core.security import hash_password
    from app.models import User
    from app.models.user_model import UserRole

    other = User(name="Other", role=UserRole.traveler, email="other@test.com", password=hash_password("secret123"))
    session.add(other)
    session.commit()
    session.refresh(other)

    data = _create_trip(client, user_token)
    trip_id = data["id"]

    # user A works
    assert client.get(f"/trip-plans/{trip_id}", headers=_auth(user_token)).status_code == 200

    # user B (other) does not — log in as other
    login = client.post("/auth/login", json={"email": "other@test.com", "password": "secret123"})
    other_token = login.json()["access_token"]
    assert client.get(f"/trip-plans/{trip_id}", headers=_auth(other_token)).status_code == 404
    assert client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(other_token)).status_code == 404


def test_update_trip_and_answers(client: TestClient, user_token: str):
    data = _create_trip(client, user_token)
    trip_id = data["id"]
    resp = client.patch(
        f"/trip-plans/{trip_id}",
        json={"budget": {"amount": 45000, "currency": "NPR", "level": "comfort"}, "answers": {"pace": "relaxed", "interests": ["food"]}},
        headers=_auth(user_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["budget"]["amount"] == 45000
    assert body["answers"]["pace"] == "relaxed"


def test_apply_edit_regenerates_affected_day(client: TestClient, user_token: str, test_destinations):
    from uuid import uuid4

    data = _create_trip(
        client, user_token, duration_days=3,
        destinations=["Pashupatinath Temple", "Annapurna Base Camp Trek"],
    )
    trip_id = data["id"]
    client.post(f"/trip-plans/{trip_id}/generate", headers=_auth(user_token))
    plan = client.get(f"/trip-plans/{trip_id}", headers=_auth(user_token)).json()
    day2 = plan["itinerary_days"][1]
    day2_id = day2["id"]

    change = {
        "intent": "modify_itinerary",
        "summary": "Made Day 2 more relaxed and moved focus to heritage",
        "trip": {"pace": "relaxed"},
        "days": [
            {
                "day_number": 2,
                "title": "Relaxed Heritage Day",
                "location": "Kathmandu",
                "notes": "Slower morning.",
                "items": [{"id": str(uuid4()), "title": "Boudhanath Stupa", "category": "cultural", "duration_hours": 2}],
            }
        ],
        "days_remove": [],
    }
    resp = client.post(f"/trip-plans/{trip_id}/apply-edit", json={"change": change}, headers=_auth(user_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert any("day_2" in a["field"] for a in body["applied"])
    updated = client.get(f"/trip-plans/{trip_id}", headers=_auth(user_token)).json()
    new_day2 = [d for d in updated["itinerary_days"] if d["day_number"] == 2][0]
    assert new_day2["title"] == "Relaxed Heritage Day"
    assert any(it["title"] == "Boudhanath Stupa" for it in new_day2["items"])
    assert updated["preferences"]["pace"] == "relaxed"
    # unchanged days preserved
    assert len(updated["itinerary_days"]) == 2


def test_trip_chat_persists_messages(client: TestClient, user_token: str, monkeypatch):
    import app.routers.trip_plan as rp

    class FakeChat:
        def __init__(self, session, trip):
            pass

        def process_message(self, message):
            return {
                "reply": "Sure — I can help with that.",
                "message_id": "00000000-0000-0000-0000-000000000001",
                "intent": "modify_itinerary",
                "proposed_plan_change": None,
                "conversation_id": "00000000-0000-0000-0000-000000000002",
            }

        def messages(self, limit=100):
            return [{"id": "x", "role": "user", "content": "hello", "intent": None, "metadata": {}, "created_at": "2026-01-01T00:00:00"}]

    monkeypatch.setattr(rp, "TripChatService", FakeChat)

    data = _create_trip(client, user_token)
    trip_id = data["id"]
    resp = client.post(f"/trip-plans/{trip_id}/messages", json={"message": "Make day 2 relaxed"}, headers=_auth(user_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["reply"] == "Sure — I can help with that."
    assert body["intent"] == "modify_itinerary"


def test_recommendations_roundtrip(client: TestClient, user_token: str):
    data = _create_trip(client, user_token)
    trip_id = data["id"]
    resp = client.post(
        f"/trip-plans/{trip_id}/recommendations",
        json={
            "kind": "restaurant",
            "title": "Tandoori Restaurant",
            "subtitle": "Nepali cuisine near Thamel",
            "payload": {"cuisine": "Nepali", "price_range": "moderate", "rating": 4},
        },
        headers=_auth(user_token),
    )
    assert resp.status_code == 201, resp.text
    recs = client.get(f"/trip-plans/{trip_id}/recommendations", headers=_auth(user_token)).json()
    assert len(recs) == 1
    assert recs[0]["title"] == "Tandoori Restaurant"


def test_delete_trip(client: TestClient, user_token: str):
    data = _create_trip(client, user_token)
    trip_id = data["id"]
    resp = client.delete(f"/trip-plans/{trip_id}", headers=_auth(user_token))
    assert resp.status_code == 200
    assert client.get(f"/trip-plans/{trip_id}", headers=_auth(user_token)).status_code == 404