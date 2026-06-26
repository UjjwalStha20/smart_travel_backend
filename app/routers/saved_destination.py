from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import SavedDestination
from app.schemas import SavedDestinationCreate, SavedDestinationUpdate
from app.services import SavedDestinationService

router = APIRouter(prefix="/saved-destinations", tags=["Saved Destinations"])

class SavedDestinationRouter:

    @router.get("/", response_model=list[SavedDestination], status_code=200)
    async def get_saved_destinations(session: SessionDep):
        return SavedDestinationService(session).get_all_saved_destinations(offset=0, limit=100)

    @router.get("/{saved_id}", response_model=SavedDestination, status_code=200)
    async def get_saved_destination_by_id(saved_id: str, session: SessionDep):
        return SavedDestinationService(session).get_saved_destination_by_id(saved_id)

    @router.post("/", response_model=SavedDestination, status_code=201)
    async def create_saved_destination(saved_data: SavedDestinationCreate, session: SessionDep):
        return SavedDestinationService(session).create_saved_destination(saved_data)

    @router.put("/{saved_id}", response_model=SavedDestination, status_code=200)
    async def update_saved_destination(saved_id: str, saved_data: SavedDestinationUpdate, session: SessionDep):
        return SavedDestinationService(session).update_saved_destination(saved_id, saved_data)

    @router.delete("/{saved_id}", status_code=200)
    async def delete_saved_destination(saved_id: str, session: SessionDep):
        return SavedDestinationService(session).delete_saved_destination(saved_id)
