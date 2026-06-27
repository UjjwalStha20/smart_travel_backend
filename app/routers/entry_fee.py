from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import EntryFee, User
from app.schemas import EntryFeeCreate, EntryFeeUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import EntryFeeService

router = APIRouter(prefix="/entry-fees", tags=["Entry Fees"])

class EntryFeeRouter:

    @router.get("/", response_model=PaginatedResponse[EntryFee], status_code=200)
    async def get_entry_fees(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return EntryFeeService(session).get_all_entry_fees(offset=offset, limit=limit)

    @router.get("/{fee_id}", response_model=EntryFee, status_code=200)
    async def get_entry_fee_by_id(fee_id: str, session: SessionDep):
        return EntryFeeService(session).get_entry_fee_by_id(fee_id)

    @router.post("/", response_model=EntryFee, status_code=201)
    async def create_entry_fee(fee_data: EntryFeeCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return EntryFeeService(session).create_entry_fee(fee_data)

    @router.put("/{fee_id}", response_model=EntryFee, status_code=200)
    async def update_entry_fee(fee_id: str, fee_data: EntryFeeUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return EntryFeeService(session).update_entry_fee(fee_id, fee_data)

    @router.delete("/{fee_id}", status_code=200)
    async def delete_entry_fee(fee_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return EntryFeeService(session).delete_entry_fee(fee_id)
