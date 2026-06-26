from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import Itinerary
from app.schemas import ItineraryCreate, ItineraryUpdate
from app.services import ItineraryService

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])

class ItineraryRouter:

    @router.get("/", response_model=list[Itinerary], status_code=200)
    async def get_itineraries(session: SessionDep):
        return ItineraryService(session).get_all_itineraries(offset=0, limit=100)

    @router.get("/{itinerary_id}", response_model=Itinerary, status_code=200)
    async def get_itinerary_by_id(itinerary_id: str, session: SessionDep):
        return ItineraryService(session).get_itinerary_by_id(itinerary_id)

    @router.post("/", response_model=Itinerary, status_code=201)
    async def create_itinerary(itinerary_data: ItineraryCreate, session: SessionDep):
        return ItineraryService(session).create_itinerary(itinerary_data)

    @router.put("/{itinerary_id}", response_model=Itinerary, status_code=200)
    async def update_itinerary(itinerary_id: str, itinerary_data: ItineraryUpdate, session: SessionDep):
        return ItineraryService(session).update_itinerary(itinerary_id, itinerary_data)

    @router.delete("/{itinerary_id}", status_code=200)
    async def delete_itinerary(itinerary_id: str, session: SessionDep):
        return ItineraryService(session).delete_itinerary(itinerary_id)
