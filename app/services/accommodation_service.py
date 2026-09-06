from fastapi import HTTPException
from sqlmodel import func, or_, select
from app.models import Accommodation


class AccommodationService:
    def __init__(self, session):
        self.session = session
    
    def get_all_accommodations(self, offset: int = 0, limit: int = 100):
        statement = select(Accommodation).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Accommodation.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}
    
    def get_accommodation_by_id(self, accommodation_id):
        accommodation = self.session.get(Accommodation, accommodation_id)
        if not accommodation:
            raise HTTPException(status_code=404, detail="Accommodation not found")
        return accommodation

    def get_by_id(self, accommodation_id):
        return self.get_accommodation_by_id(accommodation_id)

    def search_by_price_range(self, min_price=None, max_price=None, location=None, limit=10):
        statement = select(Accommodation)
        if max_price is not None:
            statement = statement.where(Accommodation.budget_price <= max_price)
        if min_price is not None:
            statement = statement.where(Accommodation.budget_price >= min_price)
        if location:
            statement = statement.where(
                or_(Accommodation.location.ilike(f"%{location}%"), Accommodation.name.ilike(f"%{location}%"))
            )
        items = self.session.exec(statement.limit(min(limit, 100))).all()
        return [item.model_dump() for item in items]
    
    def create_accommodation(self, accommodation_data: Accommodation):
        accommodation = Accommodation(**accommodation_data.model_dump())
        self.session.add(accommodation)
        self.session.commit()
        self.session.refresh(accommodation)
        return accommodation
    
    def update_accommodation(self, accommodation_id, accommodation_data: Accommodation):
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