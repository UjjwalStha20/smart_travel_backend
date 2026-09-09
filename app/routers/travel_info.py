from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select

from app.dependencies import SessionDep
from app.models import Address, Destination
from app.services.directions import get_directions
from app.services.flight_info import get_flight_options
from app.services.live_data import LiveDataError, fetch_weather
from app.services.map_service import destination_geojson
from app.services.nearby_destinations import get_nearby_destinations


router = APIRouter(prefix="/travel", tags=["Travel Info"])


def _get_coordinates(session: Session, destination_id) -> tuple[Destination, Address]:
    destination = session.get(Destination, UUID(str(destination_id)))
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    address = session.get(Address, destination.address_id) if destination.address_id else None
    if not address or address.latitude is None or address.longitude is None:
        raise HTTPException(
            status_code=422,
            detail="Destination has no GPS coordinates in its address data",
        )
    return destination, address


@router.get(
    "/weather/general",
    summary="Live weather for arbitrary coordinates",
    description="Current conditions + daily forecast for any lat/long (Open-Meteo, free).",
)
def general_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(default=5, ge=1, le=14),
):
    try:
        return fetch_weather(latitude, longitude, days=days)
    except LiveDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/destinations/{destination_id}/weather",
    summary="Live weather at a destination",
)
def destination_weather(
    destination_id: UUID,
    session: SessionDep,
    days: int = Query(default=5, ge=1, le=14),
):
    _, address = _get_coordinates(session, destination_id)
    try:
        return fetch_weather(address.latitude, address.longitude, days=days)
    except LiveDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/directions",
    summary="Point-to-point route from an origin to a destination",
    description="OSRM (free, public) driving + walking routes with distance/duration, a "
    "derived local-bus estimate, and a straight-line fallback when offline. "
    "Everything is a route drawing — there is no live traffic/booking.",
)
def directions(
    from_lat: float = Query(..., ge=-90, le=90),
    from_lon: float = Query(..., ge=-180, le=180),
    to_lat: float = Query(..., ge=-90, le=90),
    to_lon: float = Query(..., ge=-180, le=180),
    destination_name: Optional[str] = Query(default=None),
):
    return get_directions(from_lat, from_lon, to_lat, to_lon, destination_name=destination_name)


@router.get(
    "/destinations/{destination_id}/flights",
    summary="Flight & how-to-reach info (informational, no booking)",
    description="Closest airports, airlines, indicative fares/duration and booking portals. "
    "Prices are indicative and are NOT live bookings.",
)
def destination_flights(destination_id: UUID, session: SessionDep):
    return get_flight_options(session, destination_id)


@router.get(
    "/destinations/{destination_id}/map",
    summary="Offline map data (GeoJSON) for a destination",
    description="FeatureCollection with trek routes (LineStrings + elevation profile), "
    "waypoint markers, and the destination point. Frontend can render offline.",
)
def destination_map(destination_id: UUID, session: SessionDep):
    return destination_geojson(session, destination_id)


@router.get(
    "/destinations/{destination_id}/nearby",
    summary="Nearby destinations by great-circle distance",
    description="Return the closest destinations to the given one, computed via haversine "
    "distance over stored latitude/longitude coordinates.",
)
def nearby_destinations(
    destination_id: UUID,
    session: SessionDep,
    limit: int = Query(default=6, ge=1, le=20),
):
    return get_nearby_destinations(session, destination_id, limit=limit)