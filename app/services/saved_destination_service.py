from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.models import SavedDestination


class SavedDestinationService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_saved_destinations(
        self, offset: int = 0, limit: int = 100, user_id: UUID | None = None
    ):
        statement = select(SavedDestination)
        count_statement = select(func.count(SavedDestination.id))
        if user_id is not None:
            statement = statement.where(SavedDestination.user_id == user_id)
            count_statement = count_statement.where(SavedDestination.user_id == user_id)
        items = self.session.exec(statement.offset(offset).limit(limit)).all()
        total = self.session.exec(count_statement).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_saved_destination_by_id(self, saved_id: UUID) -> SavedDestination:
        saved = self.session.get(SavedDestination, saved_id)
        if not saved:
            raise HTTPException(status_code=404, detail="Saved destination not found")
        return saved

    def create_saved_destination(self, saved_data: dict) -> SavedDestination:
        existing = self.session.exec(
            select(SavedDestination).where(
                SavedDestination.user_id == saved_data["user_id"],
                SavedDestination.destination_id == saved_data["destination_id"],
            )
        ).first()
        if existing:
            return existing
        saved = SavedDestination(**saved_data)
        try:
            self.session.add(saved)
            self.session.commit()
            self.session.refresh(saved)
        except IntegrityError:
            self.session.rollback()
            existing = self.session.exec(
                select(SavedDestination).where(
                    SavedDestination.user_id == saved_data["user_id"],
                    SavedDestination.destination_id == saved_data["destination_id"],
                )
            ).first()
            if existing:
                return existing
            raise HTTPException(status_code=500, detail="Failed to save destination")
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
