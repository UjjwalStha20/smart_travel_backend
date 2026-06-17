from select import select
from typing import List

from fastapi import HTTPException
from sqlmodel import Session

from app.models.destination_model import Destination
from app.schemas.destination_schema import DestinationRead
from app.services.address_service import AddressService


class DestinationService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_destinations(self, offset: int = 0, limit: int = 10,) -> List[DestinationRead]:
        statement = select(Destination).offset(offset).limit(limit)
        destinations = self.session.exec(statement).all()
        if not destinations:
            raise HTTPException(status_code=404, detail="No destinations found")
        return destinations
    
    def get_destination_by_id(self, destination_id: str) -> Destination:
        destination = self.session.get(Destination, destination_id)
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        return destination
    
    def create_destination(self, destination_data: DestinationRead) -> Destination:
        if destination_data.address:
            address = AddressService(self.session).create_address(destination_data.address)
            if address:
                destination_data.address_id = address.id
        destination = Destination(**destination_data.model_dump())
        self.session.add(destination)
        self.session.commit()
        self.session.refresh(destination)
        return {"message": "Destination created successfully", "destination": destination}

    def update_destination(self, destination_id: str, destination_data: DestinationRead) -> Destination:
        existing_destination = self.get_destination_by_id(destination_id)
        if not existing_destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        patch = destination_data.model_dump(exclude_unset=True)
        existing_destination.sqlmodel_update(patch)

        self.session.add(existing_destination)
        self.session.commit()
        self.session.refresh(existing_destination)
        return {"message": "Destination updated successfully", "destination": existing_destination} 
    

    def delete_destination(self, destination_id: str) -> dict:
        destination = self.get_destination_by_id(destination_id)
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        self.session.delete(destination)
        self.session.commit()
        return {"message": "Destination deleted successfully"}