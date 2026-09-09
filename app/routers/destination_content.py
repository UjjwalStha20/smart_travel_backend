from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep, require_admin
from app.models import User
from app.schemas.destination_content_schema import (
    DestinationFaqCreate,
    DestinationHighlightCreate,
    DestinationThingToDoCreate,
)
from app.services import DestinationContentService
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/destinations/{destination_id}/content", tags=["Destination Content"])


class DestinationContentRouter:

    @router.get("/", status_code=200)
    async def get_content(destination_id: str, session: SessionDep):
        return DestinationContentService(session).get_content(destination_id)

    @router.post("/regenerate", status_code=200)
    async def regenerate(
        destination_id: str,
        session: SessionDep,
        admin: Annotated[User, Depends(require_admin)],
    ):
        result = DestinationContentService(session).regenerate(destination_id)
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Regenerated", target=f"Content for destination {destination_id}", type="content",
        )
        return result

    @router.post("/highlights", status_code=201)
    async def create_highlight(
        destination_id: str,
        data: DestinationHighlightCreate,
        session: SessionDep,
        admin: Annotated[User, Depends(require_admin)],
    ):
        return DestinationContentService(session).create_highlight(destination_id, data)

    @router.post("/things-to-do", status_code=201)
    async def create_thing_to_do(
        destination_id: str,
        data: DestinationThingToDoCreate,
        session: SessionDep,
        admin: Annotated[User, Depends(require_admin)],
    ):
        return DestinationContentService(session).create_thing_to_do(destination_id, data)

    @router.post("/faqs", status_code=201)
    async def create_faq(
        destination_id: str,
        data: DestinationFaqCreate,
        session: SessionDep,
        admin: Annotated[User, Depends(require_admin)],
    ):
        return DestinationContentService(session).create_faq(destination_id, data)
