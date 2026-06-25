from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep
from app.schemas.destination_schema import DestinationCreate, DestinationRead, DestinationUpdate
from app.services.destination_service import DestinationService


router = APIRouter(prefix="/destinations", tags=["destinations"])

class DestinationRouter:

    @router.get("/", status_code=200)
    def get_destinations(session: Session = Depends(get_session)):
        return DestinationService(session).get_destinations(offset=0, limit=100)
    

    @router.get("/{destination_id}")
    async def get_destination_by_id(session: SessionDep, destination_id: str):
        """Get a destination by ID."""
        # In a real application, you would fetch the destination from the database

        return DestinationService(session).get_destination_by_id(destination_id)

    @router.post("/")
    async def create_destination(session: SessionDep, destination: DestinationCreate):
        """Create a new destination."""
        # In a real application, you would save the destination to the database
        return DestinationService(session).create_destination(destination)
    
    @router.put("/{destination_id}")
    async def update_destination(session: SessionDep, destination_id: str, destination: DestinationUpdate):
        """Update a destination by ID."""
        # In a real application, you would update the destination in the database
        return DestinationService(session).update_destination(destination_id, destination)
    
    @router.delete("/{destination_id}")
    async def delete_destination(session: SessionDep, destination_id: str):
        """Delete a destination by ID."""
        # In a real application, you would delete the destination from the database
        return DestinationService(session).delete_destination(destination_id)