from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUser, SessionDep
from app.models import UserTrip
from app.schemas import UserTripCreate, UserTripUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import UserTripService

router = APIRouter(prefix="/user-trips", tags=["User Trips"])

class UserTripRouter:

    @router.get("/", response_model=PaginatedResponse[UserTrip], status_code=200)
    async def get_user_trips(session: SessionDep):
        return UserTripService(session).get_all_user_trips(offset=0, limit=100)

    @router.get("/{trip_id}", response_model=UserTrip, status_code=200)
    async def get_user_trip_by_id(trip_id: str, session: SessionDep):
        return UserTripService(session).get_user_trip_by_id(trip_id)

    @router.post("/", response_model=UserTrip, status_code=201)
    async def create_user_trip(trip_data: UserTripCreate, session: SessionDep, current_user: CurrentUser):
        data = trip_data.model_dump() | {"user_id": current_user.id}
        return UserTripService(session).create_user_trip(data)

    @router.put("/{trip_id}", response_model=UserTrip, status_code=200)
    async def update_user_trip(trip_id: str, trip_data: UserTripUpdate, session: SessionDep, current_user: CurrentUser):
        existing = UserTripService(session).get_user_trip_by_id(trip_id)
        if existing.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your trip")
        return UserTripService(session).update_user_trip(trip_id, trip_data)

    @router.delete("/{trip_id}", status_code=200)
    async def delete_user_trip(trip_id: str, session: SessionDep, current_user: CurrentUser):
        existing = UserTripService(session).get_user_trip_by_id(trip_id)
        if existing.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your trip")
        return UserTripService(session).delete_user_trip(trip_id)
