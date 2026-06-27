
from fastapi import HTTPException
from sqlmodel import func, select

from app.models import Address


class AddressService:
    def __init__(self, session):
        self.session = session

    def get_all_addresses(self, offset: int = 0, limit: int = 100):
        statement = select(Address).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Address.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_address_by_id(self, address_id):
        address = self.session.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        return address

    def get_or_create_address(self, address_data: Address):
        statement = select(Address).where(
            Address.province == address_data.province,
            Address.district == address_data.district,
            Address.latitude == address_data.latitude,
            Address.longitude == address_data.longitude,
            Address.altitude == address_data.altitude,
        )
        address = self.session.exec(statement).first()

        if not address:
            address = Address(**address_data.model_dump())
            self.session.add(address)
            self.session.commit()
            self.session.refresh(address)
        return address

    def update_address(self, address_id, address_data: Address):
        existing_address = self.get_address_by_id(address_id)
        patch = address_data.model_dump(exclude_unset=True)
        existing_address.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing_address)
        return existing_address

    def delete_address(self, address_id):
        address = self.get_address_by_id(address_id)
        self.session.delete(address)
        self.session.commit()
        return {"message": "Address deleted successfully."}