from typing import List

from fastapi import APIRouter
from fastapi.params import Depends
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep
from app.schemas import DestinationCreate, DestinationUpdate
from app.services import AttractionService


router = APIRouter(prefix="/destinations/attractions", tags=["attractions"])

class AttractionRouter:

    @router.get("/", status_code=200)
    def get_attractions(session: Session = Depends(get_session)):
        return AttractionService(session).get_attractions(offset=0, limit=100)
    

    @router.get("/{attraction_id}")
    async def get_attraction_by_id(session: SessionDep, attraction_id: str):
        """Get an attraction by ID."""
        # In a real application, you would fetch the attraction from the database

        return AttractionService(session).get_attraction_by_id(attraction_id)

    @router.post("/")
    async def create_attraction(session: SessionDep, attraction: DestinationCreate):
        """Create a new attraction."""
        # In a real application, you would save the attraction to the database
        return AttractionService(session).create_attraction(attraction)
    
    @router.put("/{attraction_id}")
    async def update_attraction(session: SessionDep, attraction_id: str, attraction: DestinationUpdate):
        """Update an attraction by ID."""
        # In a real application, you would update the attraction in the database
        return AttractionService(session).update_attraction(attraction_id, attraction)
    
    @router.delete("/{attraction_id}")
    async def delete_attraction(session: SessionDep, attraction_id: str):
        """Delete an attraction by ID."""
        # In a real application, you would delete the attraction from the database
        return AttractionService(session).delete_attraction(attraction_id)