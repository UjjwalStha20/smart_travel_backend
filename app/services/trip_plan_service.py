import json
from datetime import date, datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import (
    Destination,
    DestinationItinerary,
    DestinationThingToDo,
    TripEdit,
    TripItineraryDay,
    TripItineraryItem,
    TripPlan,
    TripPreference,
    TripRecommendation,
)
from app.models.trip_plan_model import TripDaySource, TripPlanStatus


def now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_destinations(session: Session, names: List[str]) -> List[Destination]:
    """Resolve destination names to Destination rows (case-insensitive match)."""
    found: List[Destination] = []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        dest = session.exec(
            select(Destination).where(func.lower(Destination.name) == name.lower())
        ).first()
        if dest:
            found.append(dest)
        else:
            # loose contains match as a fallback
            dest = session.exec(
                select(Destination)
                .where(func.lower(Destination.name).contains(name.lower()))
                .order_by(Destination.name)
            ).first()
            if dest:
                found.append(dest)
    return found


_ROUTE_LIKE_CATEGORIES = {"trek", "hike", "mountain"}


def _category(dest: Destination) -> str:
    cat = dest.category
    if hasattr(cat, "value"):
        cat = cat.value
    return str(cat or "").lower() or "other"


def _chunk(items: List, size: int) -> List[List]:
    size = max(int(size or 0), 1)
    return [items[i:i + size] for i in range(0, len(items), size)]


def _things_for(dest: Destination) -> List[DestinationThingToDo]:
    return list(getattr(dest, "things_to_do", []) or [])


def _fetch_itinerary_rows(session: Session, dest: Destination) -> List[DestinationItinerary]:
    return list(session.exec(
        select(DestinationItinerary)
        .where(DestinationItinerary.destination_id == dest.id)
        .order_by(DestinationItinerary.day_number.asc())
    ).all())


def build_itinerary_days(
    session: Session,
    *,
    names: List[str],
    duration_days: Optional[int],
    transportation: Optional[List[str]] = None,
    start_location: Optional[str] = None,
) -> List[dict]:
    """Compute the initial itinerary for a set of destinations WITHOUT persisting.

    Returns day dicts shaped like ``to_day_out`` (no ids/dates). Shared by both
    the authenticated plan generation and the anonymous guest preview so the
    output is always identical and driven by real destination data only.

    Modes:
    - Route-like destination categories (trek/hike/mountain): walk the
      destination's structured day-by-day itinerary rows (never repeating the
      destination and never inventing trek stages).
    - Sightseeing destinations (city/lake/cultural/religious/historical/nature…):
      one day per destination built from the destination's real activity data,
      packed several-per-day only when the trip is shorter than the chosen set.
    No durations, permits, altitudes or routes are invented.
    """
    total_days = max(int(duration_days or 4), 1)
    dests = _resolve_destinations(session, names or [])
    if not dests and start_location:
        dests = _resolve_destinations(session, [start_location])

    transport = transportation or []
    route_dests = [d for d in dests if _category(d) in _ROUTE_LIKE_CATEGORIES]
    sight_dests = [d for d in dests if _category(d) not in _ROUTE_LIKE_CATEGORIES]

    days: List[dict] = []
    counter = 1

    # Route-like destinations use their structured day-by-day itinerary.
    for dest in route_dests:
        if counter > total_days:
            break
        rows = _fetch_itinerary_rows(session, dest)
        if rows:
            for template in rows[: total_days - counter + 1]:
                location = (
                    template.overnight_location
                    or template.end_location
                    or template.start_location
                    or dest.name
                )
                items: List[dict] = []
                if (
                    template.start_location
                    and template.end_location
                    and template.start_location != template.end_location
                ):
                    items.append({
                        "title": f"Travel {template.start_location} → {template.end_location}",
                        "category": "travel",
                        "location": template.start_location,
                    })
                days.append({
                    "day_number": counter,
                    "location": location,
                    "title": template.title or dest.name,
                    "transportation": transport,
                    "estimated_duration_hours": float(template.estimated_walking_hours)
                    if template.estimated_walking_hours else None,
                    "notes": template.notes,
                    "items": items,
                })
                counter += 1
        else:
            # route-like category without structured rows: single activity day
            days.append({
                "day_number": counter,
                "location": dest.name,
                "title": dest.name,
                "transportation": transport,
                "items": [
                    {"title": t.title, "category": "adventure", "location": dest.name, "notes": t.duration}
                    for t in _things_for(dest)
                ],
            })
            counter += 1

    # Sightseeing destinations: one day per destination (grouped if short).
    remaining = total_days - (counter - 1)
    if sight_dests:
        if remaining <= 0:
            # no free days left — fold activities into the last day instead of dropping
            if days:
                last = days[-1]
                seen = {it["title"].lower() for it in last.get("items", [])}
                merged = list(last["items"])
                for dest in sight_dests:
                    for t in _things_for(dest):
                        if t.title.lower() in seen or len(merged) >= 8:
                            continue
                        seen.add(t.title.lower())
                        merged.append({
                            "title": t.title, "category": "sightseeing",
                            "location": dest.name, "notes": t.duration,
                        })
                last["items"] = merged
        elif remaining >= len(sight_dests):
            for dest in sight_dests:
                days.append({
                    "day_number": counter,
                    "location": dest.name,
                    "title": dest.name,
                    "transportation": transport,
                    "items": [
                        {"title": t.title, "category": "sightseeing", "location": dest.name, "notes": t.duration}
                        for t in _things_for(dest)
                    ],
                })
                counter += 1
        else:
            group_size = (len(sight_dests) + remaining - 1) // remaining
            for group in _chunk(sight_dests, group_size):
                names_joined = " & ".join(d.name for d in group)
                items: List[dict] = []
                for dest in group:
                    for t in _things_for(dest):
                        if len(items) >= 10:
                            break
                        items.append({
                            "title": t.title, "category": "sightseeing",
                            "location": dest.name, "notes": t.duration,
                        })
                days.append({
                    "day_number": counter,
                    "location": group[0].name,
                    "title": names_joined,
                    "transportation": transport,
                    "items": items,
                })
                counter += 1

    # Guarantee every produced day has at least one item.
    for day in days:
        if not day.get("items"):
            seen = set()
            for it in (day.get("items") or []):
                seen.add(it.get("title", "").lower())
            seen.add("")
            fallback = f"Explore {day.get('title', 'your itinerary')} at your own pace"
            if fallback.lower() not in seen:
                day.setdefault("items", []).append({
                    "title": fallback, "category": "sightseeing", "location": day.get("location"),
                })

    return days


def to_day_out(day: TripItineraryDay, items: Optional[List[TripItineraryItem]] = None) -> dict:
    if items is None:
        items = sorted(day.items, key=lambda x: x.position)
    return {
        "id": str(day.id),
        "day_number": day.day_number,
        "date": day.date.isoformat() if day.date else None,
        "location": day.location,
        "title": day.title,
        "transportation": day.transportation or [],
        "estimated_duration_hours": day.estimated_duration_hours,
        "notes": day.notes,
        "status": day.status.value if hasattr(day.status, "value") else day.status,
        "items": [
            {
                "id": str(it.id),
                "position": it.position,
                "title": it.title,
                "category": it.category,
                "location": it.location,
                "duration_hours": it.duration_hours,
                "notes": it.notes,
                "recommendation_id": str(it.recommendation_id) if it.recommendation_id else None,
            }
            for it in sorted(items, key=lambda x: x.position)
        ],
    }


def build_read(session: Session, trip: TripPlan) -> dict:
    prefs = session.exec(select(TripPreference).where(TripPreference.trip_id == trip.id)).first()
    days = session.exec(
        select(TripItineraryDay)
        .where(TripItineraryDay.trip_id == trip.id)
        .order_by(TripItineraryDay.day_number.asc())
    ).all()
    day_ids = [d.id for d in days]
    items_by_day: Dict[UUID, List[TripItineraryItem]] = {}
    if day_ids:
        all_items = session.exec(
            select(TripItineraryItem).where(TripItineraryItem.day_id.in_(day_ids))
        ).all()
        for it in all_items:
            items_by_day.setdefault(it.day_id, []).append(it)

    message_count = 0
    last_message = None
    from app.models import TripMessage
    if trip.conversation:
        msgs = session.exec(
            select(TripMessage)
            .where(TripMessage.conversation_id == trip.conversation.id)
            .order_by(TripMessage.created_at.desc())
        ).all()
        message_count = len(msgs)
        if msgs:
            m = msgs[0]
            last_message = {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "intent": m.intent,
                "metadata": m.meta or {},
                "created_at": m.created_at.isoformat(),
            }

    return {
        "id": str(trip.id),
        "user_id": str(trip.user_id),
        "name": trip.name,
        "status": trip.status.value if hasattr(trip.status, "value") else trip.status,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
        "duration_days": trip.duration_days,
        "destinations": trip.destinations or [],
        "start_location": trip.start_location,
        "travelers": trip.travelers or {},
        "budget": trip.budget or {},
        "trip_types": trip.trip_types or [],
        "transportation": trip.transportation or [],
        "accommodation": trip.accommodation,
        "preferences": trip.preferences or {},
        "special_requirements": trip.special_requirements or {},
        "summary": trip.summary,
        "created_at": trip.created_at.isoformat(),
        "updated_at": trip.updated_at.isoformat(),
        "answers": prefs.answers if prefs else {},
        "itinerary_days": [to_day_out(d, items_by_day.get(d.id)) for d in days],
        "message_count": message_count,
        "last_message": last_message,
    }


def _log_edit(session: Session, trip_id: UUID, field: str, new_value: str, origin: str = "ai", message_id: Optional[UUID] = None):
    session.add(TripEdit(trip_id=trip_id, field=field, new_value=new_value, origin=origin, message_id=message_id))


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class TripPlanService:
    def __init__(self, session: Session):
        self.session = session

    # ---- ownership ---------------------------------------------------------
    def get_trip_or_404(self, trip_id: str, user_id: UUID) -> TripPlan:
        try:
            uuid = UUID(trip_id)
        except ValueError:
            raise ValueError("Invalid trip id") from None
        trip = self.session.get(TripPlan, uuid)
        if not trip or trip.user_id != user_id:
            raise ValueError("Trip not found")
        return trip

    # ---- CRUD --------------------------------------------------------------
    def create_trip(self, user_id: UUID, data: Dict) -> TripPlan:
        trip = TripPlan(user_id=user_id, **{k: v for k, v in data.items() if k in {
            "name", "start_date", "end_date", "duration_days", "destinations",
            "start_location", "travelers", "budget", "trip_types",
            "transportation", "accommodation", "preferences", "special_requirements",
        }})
        self.session.add(trip)
        self.session.flush()
        answers = data.get("answers") or {}
        self.session.add(TripPreference(trip_id=trip.id, answers=answers))
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def update_trip(self, trip: TripPlan, data: Dict) -> TripPlan:
        allowed = {
            "name", "status", "start_date", "end_date", "duration_days",
            "destinations", "start_location", "travelers", "budget", "trip_types",
            "transportation", "accommodation", "preferences", "special_requirements", "summary",
        }
        changed = []
        for k, v in data.items():
            if k in allowed and v is not None:
                old = getattr(trip, k)
                if old != v:
                    setattr(trip, k, v)
                    changed.append((k, v))
        trip.updated_at = now()
        # map top-level structural fields into human log entries
        for k, v in changed:
            label = {
                "trip_types": "trip type",
                "transportation": "transportation",
                "accommodation": "accommodation",
                "destinations": "destinations",
                "budget": "budget",
                "travelers": "travelers",
                "preferences": "preferences",
                "pace": "pace",
            }.get(k, k.replace("_", " "))
            _log_edit(self.session, trip.id, label, json.dumps(v, default=str), origin="form")
        answers = data.get("answers")
        if answers is not None:
            pref = self.session.exec(select(TripPreference).where(TripPreference.trip_id == trip.id)).first()
            if pref:
                pref.answers = answers
                pref.updated_at = now()
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def delete_trip(self, trip: TripPlan):
        self.session.delete(trip)
        self.session.commit()

    # ---- itinerary generation ----------------------------------------------
    def generate_initial_itinerary(self, trip: TripPlan) -> List[TripItineraryDay]:
        """Generate and persist the initial itinerary from real destination data."""
        days_dicts = build_itinerary_days(
            self.session,
            names=trip.destinations or [],
            duration_days=trip.duration_days,
            transportation=trip.transportation,
            start_location=trip.start_location,
        )

        # clear any previous automatically-generated days
        existing = self.session.exec(
            select(TripItineraryDay).where(TripItineraryDay.trip_id == trip.id)
        ).all()
        for d in existing:
            self.session.delete(d)
        self.session.flush()

        new_days: List[TripItineraryDay] = []
        for d in days_dicts:
            day = TripItineraryDay(
                trip_id=trip.id,
                day_number=d["day_number"],
                location=d["location"],
                title=d["title"],
                transportation=d.get("transportation") or [],
                estimated_duration_hours=d.get("estimated_duration_hours"),
                notes=d.get("notes"),
                status=TripDaySource.generated,
            )
            self.session.add(day)
            self.session.flush()
            items = d.get("items") or []
            if items:
                for pos, raw in enumerate(items):
                    t = (raw.get("title") if isinstance(raw, dict) else str(raw)).strip()
                    if not t:
                        continue
                    self.session.add(TripItineraryItem(
                        day_id=day.id,
                        position=pos,
                        title=t,
                        category=raw.get("category") if isinstance(raw, dict) else "sightseeing",
                        location=raw.get("location") if isinstance(raw, dict) else None,
                        notes=raw.get("notes") if isinstance(raw, dict) else None,
                    ))
            else:
                self.session.add(TripItineraryItem(
                    day_id=day.id, position=0,
                    title=f"Explore {d['title']} at your own pace",
                    category="sightseeing", location=d["location"],
                ))
            new_days.append(day)

        trip.status = TripPlanStatus.planning
        trip.summary = "; ".join(trip.destinations or [])
        trip.updated_at = now()
        _log_edit(self.session, trip.id, "itinerary", f"Generated initial plan ({len(new_days)} days)", origin="system")
        self.session.commit()
        return new_days

    # ---- apply structured plan changes (from AI / edit form) ---------------
    def apply_plan_change(self, trip: TripPlan, change: Dict, message_id: Optional[UUID] = None) -> Dict:
        applied: List[Dict] = []
        trip_changes = change.get("trip") or {}
        _trip_fields = {
            "start_date", "end_date", "duration_days", "destinations",
            "start_location", "transportation", "accommodation", "name", "status",
        }
        for k, v in trip_changes.items():
            if v is None:
                continue
            if k == "budget":
                if isinstance(v, dict):
                    trip.budget = {**trip.budget, **v}
                else:
                    trip.budget = {**trip.budget, "amount": v}
            elif k == "transportation":
                trip.transportation = v if isinstance(v, list) else [v]
            elif k in _trip_fields:
                setattr(trip, k, v)
            else:
                # preferences-like changes (pace, interests, trip_types, etc.)
                if k == "trip_types":
                    trip.trip_types = v if isinstance(v, list) else [v]
                else:
                    trip.preferences = {**trip.preferences, k: v}
            applied.append({"field": k, "value": v})
            _log_edit(self.session, trip.id, k, json.dumps(v, default=str), origin="ai", message_id=message_id)

        days = self.session.exec(
            select(TripItineraryDay)
            .where(TripItineraryDay.trip_id == trip.id)
            .order_by(TripItineraryDay.day_number.asc())
        ).all()
        existing = {d.day_number: d for d in days}

        remove_numbers = change.get("days_remove") or []
        for num in sorted(remove_numbers, reverse=True):
            day = existing.get(num)
            if day:
                self.session.delete(day)
                applied.append({"field": f"day_{num}", "value": "removed"})
                _log_edit(self.session, trip.id, f"day_{num}", "removed", origin="ai", message_id=message_id)

        change_days = change.get("days") or []
        for entry in change_days:
            num = entry.get("day_number")
            day = existing.get(num)
            if day is None:
                day = TripItineraryDay(trip_id=trip.id, day_number=num or (len(days) + 1), status=TripDaySource.ai)
                self.session.add(day)
                self.session.flush()
            if entry.get("location"):
                day.location = entry.get("location")
            if entry.get("title"):
                day.title = entry.get("title")
            if entry.get("notes") is not None:
                day.notes = entry.get("notes")
            if entry.get("status"):
                day.status = entry.get("status")
            day.status = TripDaySource.ai
            # replace items when explicitly provided
            if "items" in entry and isinstance(entry["items"], list):
                for it in list(day.items):
                    self.session.delete(it)
                self.session.flush()
                for pos, raw in enumerate(entry["items"]):
                    if isinstance(raw, dict):
                        rid = raw.get("id")
                        if rid and self.session.get(TripItineraryItem, UUID(str(rid))):
                            # existing item — update instead
                            it = self.session.get(TripItineraryItem, UUID(str(rid)))
                            it.title = raw.get("title", it.title)
                            it.category = raw.get("category", it.category)
                            it.location = raw.get("location", it.location)
                            it.duration_hours = raw.get("duration_hours", it.duration_hours)
                            it.notes = raw.get("notes", it.notes)
                            it.position = pos
                        else:
                            self.session.add(TripItineraryItem(
                                day_id=day.id,
                                position=pos,
                                title=raw.get("title") or "Activity",
                                category=raw.get("category"),
                                location=raw.get("location"),
                                duration_hours=raw.get("duration_hours"),
                                notes=raw.get("notes"),
                                recommendation_id=raw.get("recommendation_id"),
                            ))
            applied.append({"field": f"day_{num}", "value": entry.get("title") or entry.get("location") or "updated"})
            _log_edit(self.session, trip.id, f"day_{num}", json.dumps(entry.get("items") or entry.get("location") or "", default=str), origin="ai", message_id=message_id)

        self.session.flush()
        # renumber
        all_days = self.session.exec(
            select(TripItineraryDay).where(TripItineraryDay.trip_id == trip.id).order_by(TripItineraryDay.day_number.asc())
        ).all()
        for idx, d in enumerate(all_days, start=1):
            if d.day_number != idx:
                d.day_number = idx
        trip.updated_at = now()
        if trip.status == TripPlanStatus.draft:
            trip.status = TripPlanStatus.planning
        self.session.commit()
        return {"applied": applied}

    def add_recommendation(self, trip: TripPlan, data: Dict) -> TripRecommendation:
        rec = TripRecommendation(trip_id=trip.id, **data)
        self.session.add(rec)
        self.session.commit()
        self.session.refresh(rec)
        return rec

    def get_recommendations(self, trip: TripPlan) -> List[TripRecommendation]:
        return self.session.exec(
            select(TripRecommendation).where(TripRecommendation.trip_id == trip.id).order_by(TripRecommendation.created_at.desc())
        ).all()

    def get_edits(self, trip: TripPlan) -> List[TripEdit]:
        return self.session.exec(
            select(TripEdit).where(TripEdit.trip_id == trip.id).order_by(TripEdit.created_at.desc())
        ).all()

    def list_trips(self, user_id: UUID, offset: int, limit: int):
        trips = self.session.exec(
            select(TripPlan).where(TripPlan.user_id == user_id).order_by(TripPlan.updated_at.desc()).offset(offset).limit(limit)
        ).all()
        total = len(trips)
        return trips, total