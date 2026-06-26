from fastapi import APIRouter

from app.dependencies import SessionDep
from app.schemas.attraction_schema import AttractionCreate, AttractionUpdate
from app.services import AttractionService


router = APIRouter(prefix="/destinations/attractions", tags=["attractions"])

class AttractionRouter:

    @router.get("/", status_code=200)
    async def get_attractions(session: SessionDep):
        return AttractionService(session).get_attractions(offset=0, limit=100)

    @router.get("/{attraction_id}")
    async def get_attraction_by_id(session: SessionDep, attraction_id: str):
        return AttractionService(session).get_attraction_by_id(attraction_id)

    @router.post("/")
    async def create_attraction(session: SessionDep, attraction: AttractionCreate):
        return AttractionService(session).create_attraction(attraction)

    @router.put("/{attraction_id}")
    async def update_attraction(session: SessionDep, attraction_id: str, attraction: AttractionUpdate):
        return AttractionService(session).update_attraction(attraction_id, attraction)

    @router.delete("/{attraction_id}")
    async def delete_attraction(session: SessionDep, attraction_id: str):
        return AttractionService(session).delete_attraction(attraction_id)