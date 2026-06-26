from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import UserTrip
from app.schemas import UserTripCreate, UserTripUpdate
from app.services import UserTripService

router = APIRouter(prefix="/user-trips", tags=["User Trips"])

class UserTripRouter:

    @router.get("/", response_model=list[UserTrip], status_code=200)
    async def get_user_trips(session: SessionDep):
        return UserTripService(session).get_all_user_trips(offset=0, limit=100)

    @router.get("/{trip_id}", response_model=UserTrip, status_code=200)
    async def get_user_trip_by_id(trip_id: str, session: SessionDep):
        return UserTripService(session).get_user_trip_by_id(trip_id)

    @router.post("/", response_model=UserTrip, status_code=201)
    async def create_user_trip(trip_data: UserTripCreate, session: SessionDep):
        return UserTripService(session).create_user_trip(trip_data)

    @router.put("/{trip_id}", response_model=UserTrip, status_code=200)
    async def update_user_trip(trip_id: str, trip_data: UserTripUpdate, session: SessionDep):
        return UserTripService(session).update_user_trip(trip_id, trip_data)

    @router.delete("/{trip_id}", status_code=200)
    async def delete_user_trip(trip_id: str, session: SessionDep):
        return UserTripService(session).delete_user_trip(trip_id)
