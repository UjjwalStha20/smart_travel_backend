"""Per-destination content (highlights, things-to-do, FAQs).

Content can be managed by admins via CRUD and is also auto-generated on first
access (and on demand) from each destination's real stored attributes so that no
destination is left with generic, cross-destination filler text.
"""
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import (
    Address,
    Destination,
    DestinationHighlight,
    DestinationThingToDo,
    DestinationFaq,
    Permit,
    RoutePoint,
)
from app.schemas.destination_content_schema import (
    DestinationHighlightCreate,
    DestinationThingToDoCreate,
    DestinationFaqCreate,
    DestinationContentRead,
)


def _best_time_label(best_time) -> str:
    if not best_time:
        return "the recommended season"
    try:
        months = list(best_time)
    except Exception:
        months = best_time
    return ", ".join(str(m) for m in months[:3]) or "the recommended season"


def _is_trek(destination: Destination) -> bool:
    category = getattr(destination, "category", "")
    return str(getattr(category, "value", category)).lower() == "trek"


def _generate_content(destination: Destination, session: Session) -> dict:
    """Build destination-specific content from stored attributes."""
    name = destination.name
    best_time = _best_time_label(destination.best_time)
    is_trek = _is_trek(destination)
    district = getattr(destination.address, "district", None) if destination.address else None
    place = getattr(destination.address, "place", None) if destination.address else None
    loc = place or district or name

    routes = list(destination.trekking_routes or [])
    route = routes[0] if routes else None
    permits = session.exec(select(Permit).where(Permit.destination_id == destination.id)).all() if destination.id else []
    permit_categories = sorted({str(p.permit_type) for p in permits})
    itinerary_days = list(destination.destination_itineraries or []) or []
    first_day = itinerary_days[0] if itinerary_days else None
    last_day = itinerary_days[-1] if itinerary_days else None

    # Highest-altitude named route point — the trek's actual wow moment.
    highest_point = None
    if route:
        route_points = session.exec(
            select(RoutePoint).where(RoutePoint.route_id == route.id)
        ).all() if getattr(route, "id", None) else []
        best = None
        best_name = None
        for rp in route_points:
            rp_address = session.get(Address, rp.address_id) if rp.address_id else None
            alt = getattr(rp_address, "altitude", None)
            if alt and (best is None or alt > best):
                best, best_name = alt, rp.name
        if best_name:
            highest_point = best_name

    highlights = []
    if is_trek and route:
        highlights.append({
            "title": f"{route.route_name or name} Trek",
            "description": f"A {route.recommended_days or 'multi'}-day trek reaching up to {route.max_altitude or 'high'}m with {route.difficulty.value if hasattr(route.difficulty, 'value') else route.difficulty} difficulty.",
            "distance_hint": f"~{route.total_distance_km} km" if route.total_distance_km else None,
            "visit_time": f"{route.recommended_days} days" if route.recommended_days else "Multi-day trek",
        })
    elif destination.attraction:
        attr = destination.attraction
        highlights.append({
            "title": f"Explore {name}",
            "description": f"Visit this landmark in {loc}; plan around {attr.visit_duration_hours or '1-2'} hours for a full visit.",
            "distance_hint": None,
            "visit_time": f"{attr.visit_duration_hours} hrs" if attr.visit_duration_hours else "1-2 hours",
        })
    else:
        highlights.append({
            "title": f"Discover {name}",
            "description": f"Immerse yourself in the landscape and culture of {loc}, one of Nepal's standout destinations.",
            "distance_hint": None,
            "visit_time": "Half to full day",
        })

    highlights.append({
        "title": f"Scenic Views Around {name}",
        "description": f"Enjoy the surrounding scenery and photo-worthy landscapes that make {name} memorable.",
        "distance_hint": "Nearby",
        "visit_time": "1-2 hours",
    })

    if permits:
        highlights.append({
            "title": "Permit & Entry Planning",
            "description": f"Permits are required here. Plan and arrange them in advance (categories: {', '.join(permit_categories[:3]) or 'standard'}).",
            "distance_hint": "On arrival",
            "visit_time": "Before you go",
        })

    things_to_do = []
    if is_trek and route:
        # 1. Getting onto the trail — a real, destination-specific first step.
        if first_day and first_day.start_location:
            things_to_do.append({
                "title": f"Arrive at {first_day.start_location} and start the trek",
                "duration": "Travel + start day",
                "difficulty": route.difficulty.value if hasattr(route.difficulty, "value") else str(route.difficulty or "moderate"),
                "cost": "Flight / vehicle + trek operator",
            })
        # 2. An actual named waypoint from the stored route or itinerary.
        mid_stop = None
        for day in itinerary_days[1:-1]:
            if day.end_location:
                mid_stop = day.end_location
                break
        if mid_stop:
            things_to_do.append({
                "title": f"Trek through {mid_stop}",
                "duration": "1-2 days",
                "difficulty": route.difficulty.value if hasattr(route.difficulty, "value") else str(route.difficulty or "moderate"),
                "cost": "Permits + daily expenses",
            })
        # 3. The summit/highlight day.
        if highest_point:
            things_to_do.append({
                "title": f"Reach {highest_point} — the route's pinnacle",
                "duration": "Peak day",
                "difficulty": "Hard",
                "cost": "Include in trek package",
            })
        elif last_day and last_day.end_location:
            things_to_do.append({
                "title": f"Finish the trek at {last_day.end_location}",
                "duration": "Last day",
                "difficulty": "Easy",
                "cost": "Transport back",
            })
        # 4. Acclimatization.
        things_to_do.append({
            "title": "Build in acclimatization days",
            "duration": "2-3 hours each",
            "difficulty": "Easy",
            "cost": "Free",
        })
    elif destination.attraction:
        attr = destination.attraction
        things_to_do.append({
            "title": f"Visit {name}",
            "duration": f"{attr.visit_duration_hours or '1-2'} hours",
            "difficulty": "Easy",
            "cost": "Entry fee",
        })
        things_to_do.append({
            "title": f"Go early or at golden hour to beat the crowd",
            "duration": "1 hour",
            "difficulty": "Easy",
            "cost": "Free",
        })
        things_to_do.append({
            "title": f"Photography walk around {loc}",
            "duration": "1-2 hours",
            "difficulty": "Easy",
            "cost": "Free",
        })
    else:
        things_to_do.append({
            "title": f"Guided Tour of {name}",
            "duration": "2-3 hours",
            "difficulty": "Easy",
            "cost": "Local guide fee",
        })
        things_to_do.append({
            "title": f"Photography Walk Around {loc}",
            "duration": "1-2 hours",
            "difficulty": "Easy",
            "cost": "Free",
        })
        things_to_do.append({
            "title": f"Cultural Immersion in {loc}",
            "duration": "Half day",
            "difficulty": "Easy",
            "cost": "Varies",
        })

    if permits:
        things_to_do.append({
            "title": "Arrange trekking permits in advance",
            "duration": "30 min",
            "difficulty": "Easy",
            "cost": "Per permit price",
        })

    faqs = [
        {
            "question": f"What is the best time to visit {name}?",
            "answer": f"The ideal window is {best_time}, when conditions are most favorable for exploring {name}.",
        },
    ]
    if is_trek and route:
        faqs.append({
            "question": f"How difficult is the trek to {name}?",
            "answer": f"The {route.route_name or 'main'} route is rated {route.difficulty.value if hasattr(route.difficulty, 'value') else route.difficulty}. Allow {route.recommended_days or 'several'} days and prepare for altitude and weather.",
        })
        faqs.append({
            "question": "Do I need a permit?",
            "answer": f"Permits are required for this trek. Obtain them from the relevant authority before departing, and carry them throughout the route.",
        })
    else:
        faqs.append({
            "question": f"How many days should I spend at {name}?",
            "answer": f"Most travelers enjoy {name} in a half to full day, with time to explore the key sights and relax.",
        })
        faqs.append({
            "question": "Is it safe to visit?",
            "answer": f"{name} is generally safe for visitors. Follow local guidance, respect customs, and stay aware in crowded areas.",
        })
    faqs.append({
        "question": f"How do I get to {name}?",
        "answer": f"Most travelers access {name} from Kathmandu by domestic flight, tourist bus, or private vehicle depending on the region and season.",
    })
    faqs.append({
        "question": "What should I pack?",
        "answer": "Layered clothing, comfortable footwear, sun protection, a reusable water bottle, and any required permits and documents.",
    })

    return {"highlights": highlights, "things_to_do": things_to_do, "faqs": faqs}


class DestinationContentService:
    def __init__(self, session: Session):
        self.session = session

    def _get_destination(self, destination_id):
        destination = self.session.exec(
            select(Destination)
            .where(Destination.id == destination_id)
            .options(
                selectinload(Destination.address),
                selectinload(Destination.attraction),
                selectinload(Destination.trekking_routes),
                selectinload(Destination.destination_itineraries),
            )
        ).first()
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        return destination

    def _has_content(self, destination_id) -> bool:
        h = self.session.exec(
            select(DestinationHighlight).where(DestinationHighlight.destination_id == destination_id)
        ).first()
        return h is not None

    def _generate_and_store(self, destination: Destination) -> dict:
        generated = _generate_content(destination, self.session)
        self.session.add_all([
            DestinationHighlight(destination_id=destination.id, position=i, **item)
            for i, item in enumerate(generated["highlights"])
        ])
        self.session.add_all([
            DestinationThingToDo(destination_id=destination.id, position=i, **item)
            for i, item in enumerate(generated["things_to_do"])
        ])
        self.session.add_all([
            DestinationFaq(destination_id=destination.id, position=i, **item)
            for i, item in enumerate(generated["faqs"])
        ])
        self.session.commit()
        return generated

    def get_content(self, destination_id) -> dict:
        destination = self._get_destination(destination_id)
        if not self._has_content(destination_id):
            self._generate_and_store(destination)

        highlights = self.session.exec(
            select(DestinationHighlight)
            .where(DestinationHighlight.destination_id == destination_id)
            .order_by(DestinationHighlight.position)
        ).all()
        things_to_do = self.session.exec(
            select(DestinationThingToDo)
            .where(DestinationThingToDo.destination_id == destination_id)
            .order_by(DestinationThingToDo.position)
        ).all()
        faqs = self.session.exec(
            select(DestinationFaq)
            .where(DestinationFaq.destination_id == destination_id)
            .order_by(DestinationFaq.position)
        ).all()

        return {
            "destination_id": destination.id,
            "destination_name": destination.name,
            "highlights": [h.model_dump() for h in highlights],
            "things_to_do": [t.model_dump() for t in things_to_do],
            "faqs": [f.model_dump() for f in faqs],
        }

    def regenerate(self, destination_id) -> dict:
        destination = self._get_destination(destination_id)
        for model in (DestinationHighlight, DestinationThingToDo, DestinationFaq):
            for row in self.session.exec(select(model).where(model.destination_id == destination_id)).all():
                self.session.delete(row)
        self.session.commit()
        self._generate_and_store(destination)
        return self.get_content(destination_id)

    # ---- Admin CRUD (highlights) ----
    def create_highlight(self, destination_id, data: DestinationHighlightCreate) -> DestinationHighlight:
        self._get_destination(destination_id)
        row = DestinationHighlight(destination_id=destination_id, **data.model_dump())
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_thing_to_do(self, destination_id, data: DestinationThingToDoCreate) -> DestinationThingToDo:
        self._get_destination(destination_id)
        row = DestinationThingToDo(destination_id=destination_id, **data.model_dump())
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_faq(self, destination_id, data: DestinationFaqCreate) -> DestinationFaq:
        self._get_destination(destination_id)
        row = DestinationFaq(destination_id=destination_id, **data.model_dump())
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row
