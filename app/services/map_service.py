"""Offline-capable map data for the frontend.

Serves everything a map widget needs as GeoJSON: destination marker, trek routes
as LineStrings, waypoint markers (with altitude/elevation, overnight stops,
linked teahouse and food cost names). The frontend can render this offline or
with bundled tiles — no external map-data API required.
"""
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    Accommodation,
    Address,
    Destination,
    FoodCost,
    RoutePoint,
    TrekkingRoute,
)


def _point(lon: float, lat: float, props: dict) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def destination_geojson(session: Session, destination_id) -> dict:
    destination = session.get(Destination, UUID(str(destination_id)))
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    features = []
    address = session.get(Address, destination.address_id) if destination.address_id else None

    if address and address.latitude is not None and address.longitude is not None:
        props = {
            "type": "destination",
            "name": destination.name,
            "category": destination.category.value,
            "district": address.district,
            "place": address.place,
            "altitude_m": address.altitude,
        }
        if destination.attraction:
            props["attraction_types"] = destination.attraction.attraction_types or []
        features.append(_point(address.longitude, address.latitude, props))

    routes = session.exec(
        select(TrekkingRoute).where(TrekkingRoute.destination_id == destination.id)
    ).all()

    for route in routes:
        route_points = session.exec(
            select(RoutePoint)
            .where(RoutePoint.route_id == route.id)
            .order_by(RoutePoint.sequence_no)
        ).all()

        coords = []
        elevation = []
        for rp in route_points:
            rp_address = session.get(Address, rp.address_id) if rp.address_id else None
            props = {
                "type": "waypoint",
                "name": rp.name,
                "sequence": rp.sequence_no,
                "overnight_stop": rp.overnight_stop,
                "walking_hours_from_previous": (
                    float(rp.walking_hours_from_previous) if rp.walking_hours_from_previous is not None else None
                ),
                "distance_from_previous_km": (
                    float(rp.distance_from_previous_km) if rp.distance_from_previous_km is not None else None
                ),
                "altitude_m": rp_address.altitude if rp_address else None,
            }
            if rp.accommodation_id and (accom := session.get(Accommodation, rp.accommodation_id)):
                props["accommodation"] = accom.name
            if rp.food_cost_id and (food := session.get(FoodCost, rp.food_cost_id)):
                props["food_cost"] = food.name

            if rp_address and rp_address.latitude is not None and rp_address.longitude is not None:
                coords.append([rp_address.longitude, rp_address.latitude])
                elevation.append(
                    [rp_address.longitude, rp_address.latitude, rp_address.altitude]
                )
                features.append(_point(rp_address.longitude, rp_address.latitude, props))

        if len(coords) >= 2:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {
                        "type": "trek_route",
                        "route_name": route.route_name,
                        "difficulty": getattr(route.difficulty, "value", route.difficulty),
                        "total_distance_km": (
                            float(route.total_distance_km) if route.total_distance_km is not None else None
                        ),
                        "recommended_days": route.recommended_days,
                        "max_altitude": route.max_altitude,
                        "elevation_profile": elevation,
                    },
                }
            )

    return {"type": "FeatureCollection", "features": features}