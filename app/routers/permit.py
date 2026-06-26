from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import SessionDep, require_admin
from app.models import Permit, User
from app.schemas import PermitCreate, PermitUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import PermitService

router = APIRouter(prefix="/permits", tags=["Permits"])

class PermitRouter:

    @router.get("/", response_model=PaginatedResponse[Permit], status_code=200)
    async def get_permits(session: SessionDep):
        return PermitService(session).get_all_permits(offset=0, limit=100)

    @router.get("/{permit_id}", response_model=Permit, status_code=200)
    async def get_permit_by_id(permit_id: str, session: SessionDep):
        return PermitService(session).get_permit_by_id(permit_id)

    @router.post("/", response_model=Permit, status_code=201)
    async def create_permit(permit_data: PermitCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return PermitService(session).create_permit(permit_data)

    @router.put("/{permit_id}", response_model=Permit, status_code=200)
    async def update_permit(permit_id: str, permit_data: PermitUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return PermitService(session).update_permit(permit_id, permit_data)

    @router.delete("/{permit_id}", status_code=200)
    async def delete_permit(permit_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return PermitService(session).delete_permit(permit_id)
