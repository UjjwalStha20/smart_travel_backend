"""Distance-based "nearby destinations" using haversine over stored coordinates."""
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Address, Destination, Photo
from app.services.flight_info import AIRPORTS


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

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


def _airport_hint(haystack: str) -> str | None:
    for airport in AIRPORTS:
        if any(kw in haystack for kw in airport["keywords"]):
            return airport["airport_code"]
    return None


def get_nearby_destinations(session: Session, destination_id, limit: int = 6):
    destination = session.get(Destination, UUID(str(destination_id)))
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    address = session.get(Address, destination.address_id) if destination.address_id else None
    if not address or address.latitude is None or address.longitude is None:
        raise HTTPException(status_code=422, detail="Destination has no GPS coordinates")

    origins = session.exec(
        select(Destination).where(Destination.id != destination.id)
    ).all()

    scored = []
    seen_places = set()
    for cand in origins:
        ca = session.get(Address, cand.address_id) if cand.address_id else None
        if not ca or ca.latitude is None or ca.longitude is None:
            continue
        key = (ca.district or "", ca.place or "", cand.name)
        if key in seen_places:
            continue
        seen_places.add(key)
        dist = haversine_km(address.latitude, address.longitude, ca.latitude, ca.longitude)
        if dist < 1.0:
            continue

        photo = session.exec(
            select(Photo).where(Photo.destination_id == cand.id)
        ).first()

        haystack = " ".join(
            filter(None, [cand.name, ca.district or "", ca.place or "", ca.province or ""])
        ).lower()

        scored.append({
            "id": str(cand.id),
            "name": cand.name,
            "category": cand.category.value if hasattr(cand.category, "value") else str(cand.category),
            "rating": cand.rating,
            "distance_km": round(dist, 1),
            "district": ca.district,
            "place": ca.place,
            "photo": photo.image_url if photo else None,
            "airport_hint": _airport_hint(haystack),
        })

    scored.sort(key=lambda x: x["distance_km"])

    # Only show places that are genuinely close. Start tight, then widen in
    # steps if there are too few matches, up to NEARBY_MAX_KM.
    radius = settings.NEARBY_MIN_KM
    while radius <= settings.NEARBY_MAX_KM:
        within = [s for s in scored if s["distance_km"] <= radius]
        if len(within) >= settings.NEARBY_MIN_RESULTS:
            scored = within
            break
        radius += 50
    else:
        scored = [s for s in scored if s["distance_km"] <= settings.NEARBY_MAX_KM]

    return scored[:limit]
