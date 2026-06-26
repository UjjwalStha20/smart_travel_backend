from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Attraction
from app.services import AddressService


class AttractionService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_attractions(self, offset: int = 0, limit: int = 10,) -> List[Attraction]:
        statement = select(Attraction).offset(offset).limit(limit)
        attractions = self.session.exec(statement).all()
        if not attractions:
            raise HTTPException(status_code=404, detail="No attractions found")
        return {"message": "Attractions retrieved successfully", "attractions": attractions}
    
    def get_attraction_by_id(self, attraction_id: str) -> Attraction:
        attraction = self.session.get(Attraction, attraction_id)
        if not attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        return {"message": "Attraction retrieved successfully", "attraction": attraction}
    
    def create_attraction(self, attraction_data: Attraction):
        attraction = Attraction(**attraction_data.model_dump())
        self.session.add(attraction)
        self.session.commit()
        self.session.refresh(attraction)
        return {"message": "Attraction created successfully", "attraction": attraction}

    def update_attraction(self, attraction_id: str, attraction_data: Attraction):
        existing_attraction = self.get_attraction_by_id(attraction_id)
        if not existing_attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        address = AddressService(self.session).get_or_create_address(attraction_data.address)
        attraction = Attraction(**attraction_data.model_dump(exclude={"address"}), address_id=address.id)
        patch = attraction.model_dump(exclude_unset=True)
        existing_attraction.sqlmodel_update(patch)
        self.session.add(existing_attraction)
        self.session.commit()
        self.session.refresh(existing_attraction)
        return {"message": "Attraction updated successfully", "attraction": existing_attraction} 
    

    def delete_attraction(self, attraction_id: str) -> dict:
        attraction = self.get_attraction_by_id(attraction_id)
        if not attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        self.session.delete(attraction)
        self.session.commit()
        return {"message": "Attraction deleted successfully"}