from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select
from sqlalchemy.orm import selectinload

from app.models import DestinationItinerary


class DestinationItineraryService:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self, offset: int = 0, limit: int = 100):
        statement = select(DestinationItinerary).options(
            selectinload(DestinationItinerary.destination)
        ).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(DestinationItinerary.id))).one()
        enriched = []
        for item in items:
            d = item.model_dump()
            if item.destination:
                d["destination_name"] = item.destination.name
            enriched.append(d)
        return {"items": enriched, "total": total, "offset": offset, "limit": limit}

    def get_by_id(self, itinerary_id: UUID) -> DestinationItinerary:
        itinerary = self.session.get(DestinationItinerary, itinerary_id)
        if not itinerary:
            raise HTTPException(status_code=404, detail="Destination itinerary not found")
        return itinerary

    def get_by_destination(self, destination_id: UUID):
        statement = (
            select(DestinationItinerary)
            .where(DestinationItinerary.destination_id == destination_id)
            .order_by(DestinationItinerary.day_number)
        )
        return self.session.exec(statement).all()

    def create(self, data: DestinationItinerary) -> DestinationItinerary:
        itinerary = DestinationItinerary(**data.model_dump())
        self.session.add(itinerary)
        self.session.commit()
        self.session.refresh(itinerary)
        return itinerary

    def update(self, itinerary_id: UUID, data: DestinationItinerary) -> DestinationItinerary:
        existing = self.get_by_id(itinerary_id)
        patch = data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete(self, itinerary_id: UUID) -> dict:
        itinerary = self.get_by_id(itinerary_id)
        self.session.delete(itinerary)
        self.session.commit()
        return {"message": "Destination itinerary deleted successfully"}
