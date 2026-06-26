from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.dependencies import CurrentUser, SessionDep
from app.models import Itinerary, UserTrip
from app.schemas import ItineraryCreate, ItineraryUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import ItineraryService

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])

class ItineraryRouter:

    @router.get("/", response_model=PaginatedResponse[Itinerary], status_code=200)
    async def get_itineraries(session: SessionDep):
        return ItineraryService(session).get_all_itineraries(offset=0, limit=100)

    @router.get("/{itinerary_id}", response_model=Itinerary, status_code=200)
    async def get_itinerary_by_id(itinerary_id: str, session: SessionDep):
        return ItineraryService(session).get_itinerary_by_id(itinerary_id)

    @router.post("/", response_model=Itinerary, status_code=201)
    async def create_itinerary(itinerary_data: ItineraryCreate, session: SessionDep, current_user: CurrentUser):
        trip = session.get(UserTrip, itinerary_data.trip_id)
        if not trip or (trip.user_id != current_user.id and current_user.role != "admin"):
            raise HTTPException(status_code=403, detail="Not your trip")
        return ItineraryService(session).create_itinerary(itinerary_data)

    @router.put("/{itinerary_id}", response_model=Itinerary, status_code=200)
    async def update_itinerary(itinerary_id: str, itinerary_data: ItineraryUpdate, session: SessionDep, current_user: CurrentUser):
        existing = ItineraryService(session).get_itinerary_by_id(itinerary_id)
        if itinerary_data.trip_id is not None and itinerary_data.trip_id != existing.trip_id:
            trip = session.get(UserTrip, itinerary_data.trip_id)
            if not trip or (trip.user_id != current_user.id and current_user.role != "admin"):
                raise HTTPException(status_code=403, detail="Not your trip")
        else:
            trip = session.get(UserTrip, existing.trip_id)
            if not trip or (trip.user_id != current_user.id and current_user.role != "admin"):
                raise HTTPException(status_code=403, detail="Not your trip")
        return ItineraryService(session).update_itinerary(itinerary_id, itinerary_data)

    @router.delete("/{itinerary_id}", status_code=200)
    async def delete_itinerary(itinerary_id: str, session: SessionDep, current_user: CurrentUser):
        existing = ItineraryService(session).get_itinerary_by_id(itinerary_id)
        trip = session.get(UserTrip, existing.trip_id)
        if not trip or (trip.user_id != current_user.id and current_user.role != "admin"):
            raise HTTPException(status_code=403, detail="Not your trip")
        return ItineraryService(session).delete_itinerary(itinerary_id)
