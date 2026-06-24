from fastapi import HTTPException
from sqlmodel import select
from app.models import Accommodation


class AccommodationService:
    def __init__(self, session):
        self.session = session
    
    def get_all_accommodations(self, offset: int = 0, limit: int = 100):
        accommodations = select(Accommodation).offset(offset).limit(limit)
        return self.session.exec(accommodations).all()
    
    def get_accommodation_by_id(self, accommodation_id):
        accommodation = self.session.get(Accommodation, accommodation_id)
        if not accommodation:
            raise HTTPException(status_code=404, detail="Accommodation not found")
        return accommodation
    
    def create_accommodation(self, accommodation_data: Accommodation):
        statement = select(Accommodation).where(
            Accommodation.budget_price == accommodation_data.budget_price,
            Accommodation.standard_price == accommodation_data.standard_price,
            Accommodation.luxury_price == accommodation_data.luxury_price
        )
        existing_accommodation = self.session.exec(statement).first()

        if existing_accommodation:
            return existing_accommodation
        else:
            accommodation = Accommodation(**accommodation_data.model_dump())
            self.session.add(accommodation)
            self.session.commit()
            self.session.refresh(accommodation)
            return accommodation
    
    def update_accommodation(self, accommodation_id, accommodation_data: Accommodation):
        statement = select(Accommodation).where(
            Accommodation.budget_price == accommodation_data.budget_price,
            Accommodation.standard_price == accommodation_data.standard_price,
            Accommodation.luxury_price == accommodation_data.luxury_price,
            Accommodation.id != accommodation_id
        )
        existing_accommodation = self.session.exec(statement).first()
        if existing_accommodation:
            self.delete_accommodation(accommodation_id)
            self.session.refresh(existing_accommodation)
            return existing_accommodation
        else:
            existing_accommodation = self.get_accommodation_by_id(accommodation_id)
            patch = accommodation_data.model_dump(exclude_unset=True)
            existing_accommodation.sqlmodel_update(patch)
            self.session.commit()
            self.session.refresh(existing_accommodation)
            return existing_accommodation
    
    def delete_accommodation(self, accommodation_id):
        accommodation = self.get_accommodation_by_id(accommodation_id)
        self.session.delete(accommodation)
        self.session.commit()
        return {"message": "Accommodation deleted successfully."}