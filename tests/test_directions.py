from unittest.mock import patch

import app.services.directions as directions


def _fake_osrm(mode, lat1, lon1, lat2, lon2):
    coords = [[lon1, lat1], [(lon1 + lon2) / 2, (lat1 + lat2) / 2], [lon2, lat2]]
    return coords, 12.0, 30.0


def test_directions_osrm_driving_and_bus(client, monkeypatch):
    monkeypatch.setattr(directions, "_osrm_route", _fake_osrm)
    response = client.get(
        "/travel/directions",
        params={
            "from_lat": 27.71, "from_lon": 85.32,
            "to_lat": 28.2, "to_lon": 83.98,
            "destination_name": "Pokhara",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["destination_name"] == "Pokhara"
    assert body["modes"]["driving"]["source"] == "osrm"
    assert body["modes"]["driving"]["distance_km"] == 12.0
    assert body["modes"]["driving"]["duration_min"] == 30
    assert body["modes"]["bus"]["note"]


def test_directions_walkable_flag(client, monkeypatch):
    monkeypatch.setattr(directions, "_osrm_route", _fake_osrm)
    close = client.get(
        "/travel/directions",
        params={"from_lat": 27.71, "from_lon": 85.32, "to_lat": 27.72, "to_lon": 85.33},
    ).json()
    assert close["walkable"] is True

    far = client.get(
        "/travel/directions",
        params={"from_lat": 27.71, "from_lon": 85.32, "to_lat": 28.2, "to_lon": 83.98},
    ).json()
    assert far["walkable"] is False


def test_directions_fallback_when_osrm_down(client):
    def boom(*args, **kwargs):
        raise directions.DirectionsError("offline")

    with patch.object(directions, "_osrm_route", side_effect=boom):
        body = client.get(
            "/travel/directions",
            params={"from_lat": 27.71, "from_lon": 85.32, "to_lat": 28.2, "to_lon": 83.98},
        ).json()
    assert body["modes"]["driving"]["source"] == "estimate"
    assert body["modes"]["driving"]["route"]["features"][0]["geometry"]["type"] == "LineString"
    assert body["straight_line_km"] > 100


def test_directions_validates_coordinates(client):
    response = client.get(
        "/travel/directions",
        params={"from_lat": 91, "from_lon": 85.32, "to_lat": 28.2, "to_lon": 83.98},
    )
    assert response.status_code == 422