from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import DestinationItinerary, User
from app.schemas import DestinationItineraryCreate, DestinationItineraryUpdate
from app.services import DestinationItineraryService
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/destination-itineraries", tags=["Destination Itineraries"])


class DestinationItineraryRouter:

    @router.get("/", status_code=200)
    async def get_all(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return DestinationItineraryService(session).get_all(offset=offset, limit=limit)

    @router.get("/by-destination/{destination_id}", status_code=200)
    async def get_by_destination(destination_id: str, session: SessionDep):
        return DestinationItineraryService(session).get_by_destination(destination_id)

    @router.get("/{itinerary_id}", status_code=200)
    async def get_by_id(itinerary_id: str, session: SessionDep):
        return DestinationItineraryService(session).get_by_id(itinerary_id)

    @router.post("/", response_model=DestinationItinerary, status_code=201)
    async def create(data: DestinationItineraryCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        result = DestinationItineraryService(session).create(data)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Created", target=f"Itinerary for destination {result.destination_name}", type="content",
        )
        return result

    @router.put("/{itinerary_id}", response_model=DestinationItinerary, status_code=200)
    async def update(itinerary_id: str, data: DestinationItineraryUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        result = DestinationItineraryService(session).update(itinerary_id, data)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Updated", target=f"Itinerary day {result.day_number} for {result.destination_name}", type="content",
        )
        return result

    @router.delete("/{itinerary_id}", status_code=200)
    async def delete(itinerary_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        existing = DestinationItineraryService(session).get_by_id(itinerary_id)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Deleted", target=f"Itinerary day {existing.day_number} for {existing.destination_name}", type="content",
        )
        return DestinationItineraryService(session).delete(itinerary_id)
