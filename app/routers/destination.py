import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep, require_admin
from app.models import User
from app.schemas.destination_schema import DestinationCreate, DestinationRead, DestinationUpdate
from app.services.destination_service import DestinationService
from app.services.activity_log_service import ActivityLogService


router = APIRouter(prefix="/destinations", tags=["destinations"])

class DestinationRouter:

    @router.get("/", status_code=200)
    def get_destinations(
        session: Session = Depends(get_session),
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        category: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        description: Optional[str] = Query(None),
        rating_min: Optional[int] = Query(None, ge=1, le=5),
        permit_required: Optional[bool] = Query(None),
        province: Optional[str] = Query(None),
        district: Optional[str] = Query(None),
        place: Optional[str] = Query(None),
    ):
        return DestinationService(session).get_destinations(
            offset=offset,
            limit=limit,
            category=category,
            name=name,
            description=description,
            rating_min=rating_min,
            permit_required=permit_required,
            province=province,
            district=district,
            place=place,
        )
    

    @router.get("/stats", status_code=200)
    def get_destinations_stats(session: Session = Depends(get_session)):
        return DestinationService(session).get_destinations_stats()

    @router.get("/{destination_id}")
    async def get_destination_by_id(session: SessionDep, destination_id: uuid.UUID):
        return DestinationService(session).get_destination_by_id(str(destination_id))

    @router.post("/")
    async def create_destination(session: SessionDep, destination: DestinationCreate, admin: Annotated[User, Depends(require_admin)]):
        """Create a new destination."""
        result = DestinationService(session).create_destination(destination)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Created", target=f"Destination: {destination.name}", type="content",
        )
        return result
    
    @router.put("/{destination_id}")
    async def update_destination(session: SessionDep, destination_id: uuid.UUID, destination: DestinationUpdate, admin: Annotated[User, Depends(require_admin)]):
        """Update a destination by ID."""
        result = DestinationService(session).update_destination(str(destination_id), destination)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Updated", target=f"Destination: {result.name}", type="content",
        )
        return result
    
    @router.delete("/{destination_id}")
    async def delete_destination(session: SessionDep, destination_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)]):
        """Delete a destination by ID."""
        name = DestinationService(session).get_destination_by_id(str(destination_id)).name
        result = DestinationService(session).delete_destination(str(destination_id))
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Deleted", target=f"Destination: {name}", type="content",
        )
        return result