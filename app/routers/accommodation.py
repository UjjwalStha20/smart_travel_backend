
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, require_admin
from app.models import Accommodation, User
from app.schemas import AccommodationCreate , AccommodationUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import AccommodationService


router = APIRouter(prefix="/accommodations", tags=["Accommodations"])

class AccommodationRouter:

    @router.get("/",response_model=PaginatedResponse[Accommodation], status_code=200)
    async def get_accommodations(session : SessionDep):
        """Get all accommodations."""
        return AccommodationService(session).get_all_accommodations(offset=0, limit=100)

    @router.get("/{accommodation_id}", response_model=Accommodation,status_code=200)
    async def get_accommodation_by_id(accommodation_id: str, session: SessionDep):
        """Get an accommodation by ID."""
        return AccommodationService(session).get_accommodation_by_id(accommodation_id)

    @router.post("/", response_model=Accommodation, status_code=201)
    async def create_accommodation(accommodation_data: AccommodationCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Create a new accommodation."""
        return AccommodationService(session).create_accommodation(accommodation_data)

    @router.put("/{accommodation_id}", response_model=Accommodation, status_code=200)
    async def update_accommodation(accommodation_id: str, accommodation_data: AccommodationUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Update an accommodation by ID."""
        return AccommodationService(session).update_accommodation(accommodation_id, accommodation_data)

    @router.delete("/{accommodation_id}", status_code=200)
    async def delete_accommodation(accommodation_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Delete an accommodation by ID."""
        return AccommodationService(session).delete_accommodation(accommodation_id)