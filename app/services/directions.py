"""Point-to-point directions using the free OSRM public routing API.

Fetches driving/walking road routes between two coordinates (GeoJSON polylines)
and derives a realistic local-bus estimate. If OSRM is unreachable it degrades to
a great-circle "as-the-crow-flies" straight line so the frontend always has a
route to draw.
"""
import math

import httpx

OSRM_URL = "https://router.project-osrm.org/route/v1/{mode}/{lon1},{lat1};{lon2},{lat2}"
OSRM_PARAMS = {"overview": "full", "geometries": "geojson", "steps": "false", "alternatives": "false"}
OSRM_TIMEOUT_SECONDS = 8.0

# A straight-line distance at or below this makes the destination walkable.
WALKABLE_MAX_KM = 5.0
# Beyond this we never ask OSRM for a walking profile (it would be absurd to walk).
MAX_OSRM_WALKING_KM = 15.0

AVG_DRIVING_KMH = 40.0   # hilly Nepali roads
AVG_BUS_KMH = 25.0
AVG_WALKING_KMH = 5.0

BUS_WAIT_MINUTES = 15.0
BUS_ROAD_OVERHEAD = 1.7


class DirectionsError(Exception):
    pass


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * earth_radius_km * math.asin(math.sqrt(a))


def _osrm_route(mode: str, lat1: float, lon1: float, lat2: float, lon2: float):
    """Return (coords, distance_km, duration_min) from the OSRM public server."""
    url = OSRM_URL.format(mode=mode, lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    response = httpx.get(url, params=OSRM_PARAMS, timeout=OSRM_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise DirectionsError(data.get("code", "osrm_error"))
    route = data["routes"][0]
    coords = route["geometry"]["coordinates"]  # [[lon, lat], ...]
    return coords, route["distance"] / 1000.0, route["duration"] / 60.0


def _estimate_route(mode: str, lat1: float, lon1: float, lat2: float, lon2: float):
    """Fallback straight-line route with a realistic travel-time estimate."""
    km = haversine_km(lat1, lon1, lat2, lon2)
    speed_kmh = {"driving": AVG_DRIVING_KMH, "bus": AVG_BUS_KMH, "walking": AVG_WALKING_KMH}[mode]
    coords = [[lon1, lat1], [lon2, lat2]]
    return coords, km, km / speed_kmh * 60.0


def _route_feature(coords, name: str):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"name": name},
            }
        ],
    }


def get_directions(from_lat: float, from_lon: float, to_lat: float, to_lon: float, destination_name: str | None = None):
    straight_line_km = haversine_km(from_lat, from_lon, to_lat, to_lon)

    # Drving route — OSRM first, straight-line fallback.
    try:
        d_coords, d_km, d_min = _osrm_route("driving", from_lat, from_lon, to_lat, to_lon)
        d_source = "osrm"
    except Exception:
        d_coords, d_km, d_min = _estimate_route("driving", from_lat, from_lon, to_lat, to_lon)
        d_source = "estimate"

    # Walking route — only OSRM when short enough to make sense.
    if straight_line_km <= MAX_OSRM_WALKING_KM:
        try:
            w_coords, w_km, w_min = _osrm_route("walking", from_lat, from_lon, to_lat, to_lon)
            w_source = "osrm"
        except Exception:
            w_coords, w_km, w_min = _estimate_route("walking", from_lat, from_lon, to_lat, to_lon)
            w_source = "estimate"
    else:
        w_coords, w_km, w_min = _estimate_route("walking", from_lat, from_lon, to_lat, to_lon)
        w_source = "estimate"

    bus_min = round(d_min * BUS_ROAD_OVERHEAD + BUS_WAIT_MINUTES)
    bus_note = (
        f"Public buses and micros follow the main road (≈{bus_min} min incl. wait time). "
        "Tourist buses from the nearest city can be booked online via Pathao Book / Sarathi."
    )

    return {
        "origin": {"latitude": from_lat, "longitude": from_lon},
        "destination": {"latitude": to_lat, "longitude": to_lon},
        "destination_name": destination_name,
        "straight_line_km": round(straight_line_km, 1),
        "walkable": straight_line_km <= WALKABLE_MAX_KM,
        "modes": {
            "driving": {
                "distance_km": round(d_km, 1),
                "duration_min": round(d_min),
                "source": d_source,
                "route": _route_feature(d_coords, "Driving route"),
            },
            "bus": {
                "distance_km": round(d_km, 1),
                "duration_min": bus_min,
                "source": "estimate",
                "route": _route_feature(d_coords, "Local bus route"),
                "note": bus_note,
            },
            "walking": {
                "distance_km": round(w_km, 1),
                "duration_min": round(w_min),
                "source": w_source,
                "route": _route_feature(w_coords, "Walking route"),
            },
        },
    }