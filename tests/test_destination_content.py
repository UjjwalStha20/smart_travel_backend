from uuid import uuid4

from app.core.config import settings


# ---------------------------------------------------------------------------
# Destination content (highlights / things-to-do / FAQs)
# ---------------------------------------------------------------------------

def test_destination_content_generated_on_first_access(client, test_destinations):
    trek = test_destinations[0]  # Annapurna Base Camp Trek
    response = client.get(f"/destinations/{trek.id}/content/")
    assert response.status_code == 200
    body = response.json()
    assert body["destination_id"] == str(trek.id)
    assert body["destination_name"] == "Annapurna Base Camp Trek"
    assert len(body["highlights"]) >= 1
    assert len(body["things_to_do"]) >= 1
    assert len(body["faqs"]) >= 3
    # Trek-specific content should mention the route
    assert any("Trek" in h["title"] for h in body["highlights"])


def test_destination_content_is_per_destination(client, test_destinations):
    attraction = test_destinations[1]  # Pashupatinath
    trek = test_destinations[0]
    body_attr = client.get(f"/destinations/{attraction.id}/content/").json()
    body_trek = client.get(f"/destinations/{trek.id}/content/").json()
    assert body_attr["faqs"][0]["question"] != body_trek["faqs"][0]["question"]
    assert body_attr["destination_name"] == "Pashupatinath Temple"
    assert not any("Trek" in h["title"] for h in body_attr["highlights"])


def test_destination_content_unknown_destination(client):
    assert client.get(f"/destinations/{str(uuid4())}/content/").status_code == 404


def test_admin_can_add_highlight(client, test_destinations, admin_token):
    dest = test_destinations[0]
    response = client.post(
        f"/destinations/{dest.id}/content/highlights",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "Custom Highlight", "description": "Added by admin", "position": 9},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Custom Highlight"


def test_non_admin_cannot_add_highlight(client, test_destinations, user_token):
    dest = test_destinations[0]
    response = client.post(
        f"/destinations/{dest.id}/content/highlights",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"title": "Nope", "description": "Not allowed"},
    )
    assert response.status_code == 403


def test_content_persistence_after_generation(client, session, test_destinations):
    dest = test_destinations[0]
    first = client.get(f"/destinations/{dest.id}/content/").json()
    second = client.get(f"/destinations/{dest.id}/content/").json()
    # Same rows should be persisted & re-fetched (counts match)
    assert len(second["highlights"]) == len(first["highlights"])
    assert second["highlights"][0]["id"] == first["highlights"][0]["id"]


# ---------------------------------------------------------------------------
# Nearby destinations (haversine distance)
# ---------------------------------------------------------------------------

def test_nearby_destinations_returns_distance_sorted(client, test_destinations):
    pashupatinath = test_destinations[1]  # Kathmandu (27.71, 85.32)
    response = client.get(f"/travel/destinations/{pashupatinath.id}/nearby")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) == 2  # both others are ~92km away in Kaski
    distances = [r["distance_km"] for r in results]
    assert distances == sorted(distances)
    assert results[0]["distance_km"] > 0
    assert results[0]["id"] != str(pashupatinath.id)
    assert results[0]["name"]


def test_nearby_destinations_unknown(client):
    assert client.get(f"/travel/destinations/{str(uuid4())}/nearby").status_code == 404


def test_nearby_destinations_prefers_a_close_cluster(session, client, test_destinations):
    """A close cluster is kept while distant places (~92km+) are dropped."""
    from app.models import Address, Destination, DestinationCategory

    close = [
        ("Bhaktapur Durbar Square", "Bhaktapur", 27.672, 85.428),
        ("Swayambhunath Stupa", "Kathmandu", 27.715, 85.290),
        ("Boudhanath Stupa", "Kathmandu", 27.721, 85.362),
    ]
    for name, place, lat, lon in close:
        addr = Address(
            province="Bagmati", district="Kathmandu", place=place,
            latitude=lat, longitude=lon, altitude=1400,
        )
        session.add(addr)
        session.flush()
        session.add(Destination(
            name=name, category=DestinationCategory.attraction,
            description="Close by", best_time=["October"], permit_required=False,
            rating=5, address_id=addr.id,
        ))
    session.commit()

    pashupatinath = test_destinations[1]  # Kathmandu (27.71, 85.32)
    response = client.get(f"/travel/destinations/{pashupatinath.id}/nearby")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 3
    assert all(r["distance_km"] < settings.NEARBY_MIN_KM for r in results)
    assert all(r["name"] != "Annapurna Base Camp Trek" for r in results)
    assert results[0]["distance_km"] <= results[1]["distance_km"]


def test_nearby_destinations_limit(client, test_destinations):
    pashupatinath = test_destinations[1]
    response = client.get(f"/travel/destinations/{pashupatinath.id}/nearby", params={"limit": 1})
    assert response.status_code == 200
    assert len(response.json()) == 1