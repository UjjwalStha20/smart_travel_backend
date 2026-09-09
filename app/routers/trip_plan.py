from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chat.trip_chat_service import TripChatService
from app.dependencies import CurrentUser, SessionDep
from app.models import TripPlan
from app.schemas import (
    AddRecommendationRequest,
    PlanAcceptResponse,
    PlanGenerateResponse,
    TripChatRequest,
    TripChatResponse,
    TripEditOut,
    TripMessageOut,
    TripPlanCreate,
    TripPlanRead,
    TripPlanUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.trip_plan_schema import (
    ApplyEditRequest,
    ApplyEditResponse,
    AddRecommendationResponse,
    PlanPreviewRequest,
    PlanPreviewResponse,
    TripRecommendationOut,
)
from app.services.trip_plan_service import TripPlanService, build_itinerary_days, build_read

router = APIRouter(prefix="/trip-plans", tags=["Trip Plans"])


class TripPlanCreateBody(TripPlanCreate):
    answers: Optional[Dict] = None


class TripPlanUpdateBody(TripPlanUpdate):
    answers: Optional[Dict] = None


def _get_owned_trip(service: TripPlanService, trip_id: str, user_id: UUID) -> TripPlan:
    try:
        return service.get_trip_or_404(trip_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Trip plan not found") from None


@router.get("/", response_model=PaginatedResponse[TripPlanRead], status_code=200)
def list_trip_plans(session: SessionDep, current_user: CurrentUser, offset: int = 0, limit: int = 100):
    service = TripPlanService(session)
    trips, _total = service.list_trips(current_user.id, offset=offset, limit=limit)
    items = [build_read(session, t) for t in trips]
    return {"items": items, "total": len(items)}


@router.post("/", response_model=TripPlanRead, status_code=201)
def create_trip_plan(body: TripPlanCreateBody, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    data = body.model_dump()
    answers = data.pop("answers", None) or {}
    trip = service.create_trip(current_user.id, data)
    if answers:
        trip_service = TripPlanService(session)
        trip = trip_service.update_trip(trip, {"answers": answers})
    return build_read(session, trip)


@router.get("/{trip_id}", response_model=TripPlanRead, status_code=200)
def get_trip_plan(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    return build_read(session, trip)


@router.post("/preview", response_model=PlanPreviewResponse, status_code=200)
def preview_trip_plan(body: PlanPreviewRequest, session: SessionDep):
    days = build_itinerary_days(
        session,
        names=body.destinations,
        duration_days=body.duration_days,
        transportation=body.transportation,
        start_location=body.start_location,
    )
    return {"days": days, "status": "preview"}


@router.patch("/{trip_id}", response_model=TripPlanRead, status_code=200)
def update_trip_plan(trip_id: str, body: TripPlanUpdateBody, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    trip = service.update_trip(trip, body.model_dump(exclude_none=True))
    return build_read(session, trip)


@router.delete("/{trip_id}", status_code=200)
def delete_trip_plan(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    service.delete_trip(trip)
    return {"message": "Trip plan deleted"}


@router.post("/{trip_id}/generate", response_model=PlanGenerateResponse, status_code=200)
def generate_trip_plan(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    service.generate_initial_itinerary(trip)
    return {"trip": build_read(session, trip), "status": "generated"}


@router.post("/{trip_id}/accept", response_model=PlanAcceptResponse, status_code=200)
def accept_trip_plan(trip_id: str, session: SessionDep, current_user: CurrentUser):
    from app.models.trip_plan_model import TripPlanStatus

    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    trip = service.update_trip(trip, {"status": TripPlanStatus.accepted})
    return {"trip": build_read(session, trip), "status": "accepted"}


@router.post("/{trip_id}/messages", response_model=TripChatResponse, status_code=200)
def send_trip_message(trip_id: str, body: TripChatRequest, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    chat = TripChatService(session, trip)
    return chat.process_message(body.message)


@router.get("/{trip_id}/messages", response_model=List[TripMessageOut], status_code=200)
def list_trip_messages(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    chat = TripChatService(session, trip)
    return chat.messages()


@router.post("/{trip_id}/apply-edit", response_model=ApplyEditResponse, status_code=200)
def apply_trip_edit(trip_id: str, body: ApplyEditRequest, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    result = service.apply_plan_change(trip, body.change.model_dump(exclude_none=True), message_id=body.message_id)
    read = build_read(session, trip)
    return {"applied": result["applied"], "days": read["itinerary_days"], "trip": read}


@router.get("/{trip_id}/edits", response_model=List[TripEditOut], status_code=200)
def list_trip_edits(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    return service.get_edits(trip)


@router.post("/{trip_id}/recommendations", response_model=AddRecommendationResponse, status_code=201)
def add_trip_recommendation(trip_id: str, body: AddRecommendationRequest, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    rec = service.add_recommendation(trip, body.model_dump())
    return {"id": rec.id, "trip_id": trip.id, "kind": rec.kind, "title": rec.title}


@router.get("/{trip_id}/recommendations", response_model=List[TripRecommendationOut], status_code=200)
def list_trip_recommendations(trip_id: str, session: SessionDep, current_user: CurrentUser):
    service = TripPlanService(session)
    trip = _get_owned_trip(service, trip_id, current_user.id)
    recs = service.get_recommendations(trip)
    return [
        {
            "id": r.id,
            "kind": r.kind,
            "destination_id": r.destination_id,
            "title": r.title,
            "subtitle": r.subtitle,
            "payload": r.payload or {},
            "source": r.source,
            "created_at": r.created_at.isoformat(),
        }
        for r in recs
    ]