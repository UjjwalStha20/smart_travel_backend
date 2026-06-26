from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Itinerary


class ItineraryService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_itineraries(self, offset: int = 0, limit: int = 100):
        statement = select(Itinerary).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_itinerary_by_id(self, itinerary_id: UUID) -> Itinerary:
        itinerary = self.session.get(Itinerary, itinerary_id)
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        return itinerary

    def create_itinerary(self, itinerary_data: Itinerary) -> Itinerary:
        itinerary = Itinerary(**itinerary_data.model_dump())
        self.session.add(itinerary)
        self.session.commit()
        self.session.refresh(itinerary)
        return itinerary

    def update_itinerary(self, itinerary_id: UUID, itinerary_data: Itinerary) -> Itinerary:
        existing = self.get_itinerary_by_id(itinerary_id)
        patch = itinerary_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_itinerary(self, itinerary_id: UUID) -> dict:
        itinerary = self.get_itinerary_by_id(itinerary_id)
        self.session.delete(itinerary)
        self.session.commit()
        return {"message": "Itinerary deleted successfully"}
