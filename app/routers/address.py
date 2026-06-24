

from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models.address_model import Address
from app.schemas.address_schema import AddressCreate, AddressUpdate
from app.services.address_service import AddressService


router = APIRouter(prefix="/addresses", tags=["addresses"])

class Addressrouter:

    @router.get("/", response_model=list[Address], status_code=200)
    async def get_addresses(session: SessionDep):
        """Get all addresses."""
        return AddressService(session).get_all_addresses(offset=0, limit=100)

    @router.get("/{address_id}")
    async def get_address_by_id(address_id: str, session: SessionDep):
        """Get an address by ID."""
        return AddressService(session).get_address_by_id(address_id)

    @router.post("/")
    async def create_address(address: AddressCreate, session: SessionDep) -> Address:
        """Create a new address."""
        return AddressService(session).get_or_create_address(address)

    @router.put("/{address_id}")
    async def update_address(address_id: str, address_data: AddressUpdate, session: SessionDep):
        """Update an address by ID."""
        return AddressService(session).update_address(address_id, address_data)

    @router.delete("/{address_id}")
    async def delete_address(address_id: str, session: SessionDep):
        """Delete an address by ID."""
        return AddressService(session).delete_address(address_id)