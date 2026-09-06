import pytest

from uuid import uuid4

from app.models import Address, RoutePoint, TrekkingRoute


FAKE_WEATHER = {
    "latitude": 28.2,
    "longitude": 83.98,
    "timezone": "auto",
    "source": "Open-Meteo",
    "current": {
        "time": "2026-09-06T12:00",
        "condition": "Partly cloudy",
        "temperature_c": 18.0,
        "apparent_temperature_c": 17.5,
        "humidity_percent": 60.0,
        "precipitation_mm": 0.0,
        "wind_speed_kmh": 8.0,
    },
    "daily": [
        {
            "date": "2026-09-06",
            "condition": "Rain",
            "max_temp_c": 20.0,
            "min_temp_c": 12.0,
            "precipitation_probability": 80,
            "precipitation_mm": 5.0,
            "wind_speed_kmh": 12.0,
        }
    ],
}


@pytest.fixture
def fake_weather(monkeypatch):
    monkeypatch.setattr(
        "app.routers.travel_info.fetch_weather",
        lambda latitude, longitude, days=5: FAKE_WEATHER,
    )
    monkeypatch.setattr(
        "app.chat.tools.weather_tool.fetch_weather",
        lambda latitude, longitude, days=5: FAKE_WEATHER,
    )
    return FAKE_WEATHER


# ---------------------------------------------------------------------------
# Weather endpoints (network mocked)
# ---------------------------------------------------------------------------

def test_weather_general_endpoint(client, fake_weather):
    response = client.get("/travel/weather/general", params={"latitude": 28.2, "longitude": 83.98})
    assert response.status_code == 200
    assert response.json()["source"] == "Open-Meteo"
    assert response.json()["current"]["temperature_c"] == 18.0


def test_destination_weather_endpoint(client, fake_weather, test_destinations):
    trek = test_destinations[0]
    response = client.get(f"/travel/destinations/{trek.id}/weather", params={"days": 3})
    assert response.status_code == 200
    assert "destination" not in response.json()  # API shape confirmed intact
    assert response.json()["daily"][0]["condition"] == "Rain"


def test_weather_unknown_destination(client, fake_weather):
    response = client.get(f"/travel/destinations/{str(uuid4())}/weather")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Flight info (offline, deterministic)
# ---------------------------------------------------------------------------

def test_flights_for_kathmandu_destination(client, test_destinations):
    pashupatinath = test_destinations[1]  # Pashupatinath -> Kathmandu
    response = client.get(f"/travel/destinations/{pashupatinath.id}/flights")
    assert response.status_code == 200
    body = response.json()
    assert body["options"][0]["airport_code"] == "KTM"
    assert body["how_to_reach"]


def test_flights_for_trek_destination(client, test_destinations):
    annapurna = test_destinations[0]  # ABC trek -> Pokhara
    response = client.get(f"/travel/destinations/{annapurna.id}/flights")
    assert response.status_code == 200
    assert response.json()["options"][0]["airport_code"] == "PKR"


def test_flight_tool(session, test_destinations):
    from app.chat.tools.flight_tool import FlightTool
    result = FlightTool(session).get_flight_options(str(test_destinations[1].id))
    assert "error" not in result
    assert result["options"][0]["airport_code"] == "KTM"


# ---------------------------------------------------------------------------
# Offline map data (GeoJSON)
# ---------------------------------------------------------------------------

def test_destination_map_geojson(client, session, test_destinations):
    trek = test_destinations[0]
    route = TrekkingRoute(
        destination_id=trek.id, route_name="Map Test Route",
        difficulty="easy", recommended_days=1,
    )
    session.add(route)
    session.flush()
    coords = [("Stop A", 28.1, 84.0, 800), ("Stop B", 28.2, 84.1, 1200), ("Stop C", 28.3, 84.0, 2000)]
    for i, (name, lat, lon, alt) in enumerate(coords, start=1):
        addr = Address(province="Gandaki", district="Kaski", place=name, latitude=lat, longitude=lon, altitude=alt)
        session.add(addr)
        session.flush()
        session.add(RoutePoint(route_id=route.id, sequence_no=i, name=name, address_id=addr.id, overnight_stop=(i == 2)))
    session.commit()

    response = client.get(f"/travel/destinations/{trek.id}/map")
    assert response.status_code == 200
    fc = response.json()
    assert fc["type"] == "FeatureCollection"

    trek_feature = next(f for f in fc["features"] if f["properties"]["type"] == "trek_route")
    assert trek_feature["geometry"]["type"] == "LineString"
    assert len(trek_feature["geometry"]["coordinates"]) == 3
    assert [pt[2] for pt in trek_feature["properties"]["elevation_profile"]] == [800, 1200, 2000]

    waypoints = [f for f in fc["features"] if f["properties"]["type"] == "waypoint"]
    assert len(waypoints) == 3
    assert waypoints[1]["properties"]["overnight_stop"] is True


def test_weather_tool(session, test_destinations, fake_weather):
    from app.chat.tools.weather_tool import WeatherTool
    result = WeatherTool(session).get_destination_weather(str(test_destinations[0].id), days=5)
    assert "error" not in result
    assert result["current"]["condition"] == "Partly cloudy"
    assert result["destination"] == "Annapurna Base Camp Trek"