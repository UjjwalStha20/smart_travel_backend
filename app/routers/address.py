

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import User
from app.models.address_model import Address
from app.schemas.address_schema import AddressCreate, AddressUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.address_service import AddressService


router = APIRouter(prefix="/addresses", tags=["addresses"])

class Addressrouter:

    @router.get("/", response_model=PaginatedResponse[Address], status_code=200)
    async def get_addresses(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        """Get all addresses."""
        return AddressService(session).get_all_addresses(offset=offset, limit=limit)

    @router.get("/{address_id}")
    async def get_address_by_id(address_id: str, session: SessionDep):
        """Get an address by ID."""
        return AddressService(session).get_address_by_id(address_id)

    @router.post("/")
    async def create_address(address: AddressCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]) -> Address:
        """Create a new address."""
        return AddressService(session).get_or_create_address(address)

    @router.put("/{address_id}")
    async def update_address(address_id: str, address_data: AddressUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Update an address by ID."""
        return AddressService(session).update_address(address_id, address_data)

    @router.delete("/{address_id}")
    async def delete_address(address_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Delete an address by ID."""
        return AddressService(session).delete_address(address_id)