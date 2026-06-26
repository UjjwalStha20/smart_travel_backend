import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep, require_admin
from app.models import User
from app.schemas.destination_schema import DestinationCreate, DestinationRead, DestinationUpdate
from app.services.destination_service import DestinationService


router = APIRouter(prefix="/destinations", tags=["destinations"])

class DestinationRouter:

    @router.get("/", status_code=200)
    def get_destinations(session: Session = Depends(get_session)):
        return DestinationService(session).get_destinations(offset=0, limit=100)
    

    @router.get("/{destination_id}")
    async def get_destination_by_id(session: SessionDep, destination_id: uuid.UUID):
        return DestinationService(session).get_destination_by_id(str(destination_id))

    @router.post("/")
    async def create_destination(session: SessionDep, destination: DestinationCreate, admin: Annotated[User, Depends(require_admin)]):
        """Create a new destination."""
        return DestinationService(session).create_destination(destination)
    
    @router.put("/{destination_id}")
    async def update_destination(session: SessionDep, destination_id: uuid.UUID, destination: DestinationUpdate, admin: Annotated[User, Depends(require_admin)]):
        """Update a destination by ID."""
        return DestinationService(session).update_destination(str(destination_id), destination)
    
    @router.delete("/{destination_id}")
    async def delete_destination(session: SessionDep, destination_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)]):
        """Delete a destination by ID."""
        return DestinationService(session).delete_destination(str(destination_id))