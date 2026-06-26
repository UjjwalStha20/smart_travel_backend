from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, require_admin
from app.models import User
from app.models.attraction_model import Attraction
from app.schemas.attraction_schema import AttractionCreate, AttractionUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import AttractionService


router = APIRouter(prefix="/attractions", tags=["attractions"])

class AttractionRouter:

    @router.get("/", response_model=PaginatedResponse[Attraction], status_code=200)
    async def get_attractions(session: SessionDep):
        return AttractionService(session).get_attractions(offset=0, limit=100)

    @router.get("/{attraction_id}", response_model=Attraction)
    async def get_attraction_by_id(attraction_id: str, session: SessionDep):
        return AttractionService(session).get_attraction_by_id(attraction_id)

    @router.post("/")
    async def create_attraction(session: SessionDep, attraction: AttractionCreate, admin: Annotated[User, Depends(require_admin)]):
        return AttractionService(session).create_attraction(attraction)

    @router.put("/{attraction_id}")
    async def update_attraction(session: SessionDep, attraction_id: str, attraction: AttractionUpdate, admin: Annotated[User, Depends(require_admin)]):
        return AttractionService(session).update_attraction(attraction_id, attraction)

    @router.delete("/{attraction_id}")
    async def delete_attraction(session: SessionDep, attraction_id: str, admin: Annotated[User, Depends(require_admin)]):
        return AttractionService(session).delete_attraction(attraction_id)