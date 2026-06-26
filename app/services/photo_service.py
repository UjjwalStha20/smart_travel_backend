from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Photo


class PhotoService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_photos(self, offset: int = 0, limit: int = 100):
        statement = select(Photo).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_photo_by_id(self, photo_id: UUID) -> Photo:
        photo = self.session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        return photo

    def create_photo(self, photo_data: Photo) -> Photo:
        photo = Photo(**photo_data.model_dump())
        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)
        return photo

    def update_photo(self, photo_id: UUID, photo_data: Photo) -> Photo:
        existing = self.get_photo_by_id(photo_id)
        patch = photo_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_photo(self, photo_id: UUID) -> dict:
        photo = self.get_photo_by_id(photo_id)
        self.session.delete(photo)
        self.session.commit()
        return {"message": "Photo deleted successfully"}
