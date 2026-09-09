from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import Attraction, Destination

class AttractionService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_attractions(self, offset: int = 0, limit: int = 100):
        statement = select(Attraction).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Attraction.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_by_destination_id(self, destination_id: str):
        statement = select(Attraction).where(Attraction.destination_id == UUID(str(destination_id)))
        return self.session.exec(statement).first()

    def search_by_type(self, attraction_type: str, limit: int = 10):
        attractions = self.session.exec(select(Attraction)).all()
        results = []
        for attraction in attractions:
            types = attraction.attraction_types or []
            if any(attraction_type.lower() == t.lower() for t in types):
                destination = self.session.get(Destination, attraction.destination_id)
                address = getattr(destination, "address", None) if destination else None
                results.append({
                    "id": attraction.id,
                    "name": destination.name if destination else None,
                    "address": address.place if address else None,
                    "attraction_types": types,
                    "opening_hours": attraction.opening_hours,
                    "visit_duration_hours": attraction.visit_duration_hours,
                })
                if len(results) >= limit:
                    break
        return results
    
    def get_attraction_by_id(self, attraction_id: str):
        attraction = self.session.get(Attraction, attraction_id)
        if not attraction:
            raise HTTPException(status_code=404, detail="Attraction not found")
        return attraction
    
    def create_attraction(self, attraction_data):
        payload = attraction_data.model_dump()
        entry_fees = payload.pop("entry_fees", None)
        attraction = Attraction(**payload)
        self.session.add(attraction)
        self.session.commit()
        self.session.refresh(attraction)

        if entry_fees:
            from app.models import EntryFee
            for fee in entry_fees:
                self.session.add(EntryFee(attraction_id=attraction.id, **fee))
            self.session.commit()

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