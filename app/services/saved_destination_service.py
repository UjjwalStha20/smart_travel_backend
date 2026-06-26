from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import SavedDestination


class SavedDestinationService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_saved_destinations(self, offset: int = 0, limit: int = 100):
        statement = select(SavedDestination).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_saved_destination_by_id(self, saved_id: UUID) -> SavedDestination:
        saved = self.session.get(SavedDestination, saved_id)
        if not saved:
            raise HTTPException(status_code=404, detail="Saved destination not found")
        return saved

    def create_saved_destination(self, saved_data: SavedDestination) -> SavedDestination:
        saved = SavedDestination(**saved_data.model_dump())
        self.session.add(saved)
        self.session.commit()
        self.session.refresh(saved)
        return saved

    def update_saved_destination(self, saved_id: UUID, saved_data: SavedDestination) -> SavedDestination:
        existing = self.get_saved_destination_by_id(saved_id)
        patch = saved_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_saved_destination(self, saved_id: UUID) -> dict:
        saved = self.get_saved_destination_by_id(saved_id)
        self.session.delete(saved)
        self.session.commit()
        return {"message": "Saved destination deleted successfully"}
