from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Attraction

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
    
    def create_attraction(self, attraction_data):
        attraction = Attraction(**attraction_data.model_dump())
        self.session.add(attraction)
        self.session.commit()
        self.session.refresh(attraction)
        return {"message": "Attraction created successfully", "attraction": attraction}

    def update_attraction(self, attraction_id: str, attraction_data):
        existing = self.session.get(Attraction, attraction_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Attraction not found")
        patch = attraction_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return {"message": "Attraction updated successfully", "attraction": existing}

    def delete_attraction(self, attraction_id: str) -> dict:
        attraction = self.session.get(Attraction, attraction_id)
        if not attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        self.session.delete(attraction)
        self.session.commit()
        return {"message": "Attraction deleted successfully"}