

from fastapi import HTTPException

from app.models.address_model import Address


class AddressService:
    def __init__(self, session):
        self.session = session

    def get_address_by_id(self, address_id):
        address = self.session.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        return address

    def create_address(self, address_data: Address) -> Address:
        address = Address(**address_data.dict())
        self.session.add(address)
        self.session.commit()
        self.session.refresh(address)
        return address

    def update_address(self, address_id, address_data):
        address = self.get_address_by_id(address_id)
        for key, value in address_data.items():
            setattr(address, key, value)
        self.session.commit()
        self.session.refresh(address)
        return address

    def delete_address(self, address_id):
        address = self.get_address_by_id(address_id)
        self.session.delete(address)
        self.session.commit()
        return address