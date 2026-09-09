from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentUser, SessionDep
from app.models import SavedDestination
from app.schemas import SavedDestinationCreate, SavedDestinationUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import SavedDestinationService

router = APIRouter(prefix="/saved-destinations", tags=["Saved Destinations"])

class SavedDestinationRouter:

    @router.get("/", response_model=PaginatedResponse[SavedDestination], status_code=200)
    async def get_saved_destinations(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return SavedDestinationService(session).get_all_saved_destinations(offset=offset, limit=limit)

    @router.get("/mine", response_model=PaginatedResponse[SavedDestination], status_code=200)
    async def get_my_saved_destinations(session: SessionDep, current_user: CurrentUser, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return SavedDestinationService(session).get_all_saved_destinations(
            user_id=current_user.id, offset=offset, limit=limit
        )

    @router.get("/{saved_id}", response_model=SavedDestination, status_code=200)
    async def get_saved_destination_by_id(saved_id: str, session: SessionDep):
        return SavedDestinationService(session).get_saved_destination_by_id(saved_id)

    @router.post("/", response_model=SavedDestination, status_code=201)
    async def create_saved_destination(saved_data: SavedDestinationCreate, session: SessionDep, current_user: CurrentUser):
        data = saved_data.model_dump() | {"user_id": current_user.id}
        return SavedDestinationService(session).create_saved_destination(data)

    @router.delete("/{saved_id}", status_code=200)
    async def delete_saved_destination(saved_id: str, session: SessionDep, current_user: CurrentUser):
        existing = SavedDestinationService(session).get_saved_destination_by_id(saved_id)
        if existing.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your saved destination")
        return SavedDestinationService(session).delete_saved_destination(saved_id)
