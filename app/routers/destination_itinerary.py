from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.models import DestinationItinerary
from app.schemas import DestinationItineraryCreate, DestinationItineraryUpdate
from app.services import DestinationItineraryService

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
    async def create(data: DestinationItineraryCreate, session: SessionDep):
        return DestinationItineraryService(session).create(data)

    @router.put("/{itinerary_id}", response_model=DestinationItinerary, status_code=200)
    async def update(itinerary_id: str, data: DestinationItineraryUpdate, session: SessionDep):
        return DestinationItineraryService(session).update(itinerary_id, data)

    @router.delete("/{itinerary_id}", status_code=200)
    async def delete(itinerary_id: str, session: SessionDep):
        return DestinationItineraryService(session).delete(itinerary_id)
