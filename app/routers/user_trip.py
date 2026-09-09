from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentUser, SessionDep
from app.models import UserTrip
from app.schemas import UserTripCreate, UserTripUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import UserTripService

router = APIRouter(prefix="/user-trips", tags=["User Trips"])

class UserTripRouter:

    @router.get("/", response_model=PaginatedResponse[UserTrip], status_code=200)
    async def get_user_trips(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return UserTripService(session).get_all_user_trips(offset=offset, limit=limit)

    @router.get("/mine", response_model=PaginatedResponse[UserTrip], status_code=200)
    async def get_my_user_trips(session: SessionDep, current_user: CurrentUser, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return UserTripService(session).get_all_user_trips(
            user_id=current_user.id, offset=offset, limit=limit
        )

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
