import os
import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.core.config import settings
from app.models import Photo


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class PhotoService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_photos(self, offset: int = 0, limit: int = 100):
        statement = select(Photo).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Photo.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_photo_by_id(self, photo_id: UUID) -> Photo:
        photo = self.session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        return photo

    def create_photo(self, photo_data: dict) -> Photo:
        photo = Photo(**photo_data)
        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)
        return photo

    def create_photo_from_upload(self, destination_id: UUID, user_id: UUID, filename: str, content: bytes, caption: str | None = None, is_featured: bool = False) -> Photo:
        ext = os.path.splitext(filename or ".jpg")[1]
        saved_name = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_DIR, saved_name)

        with open(filepath, "wb") as f:
            f.write(content)

        image_url = f"/uploads/{saved_name}"
        photo = Photo(destination_id=destination_id, uploaded_by=user_id, image_url=image_url, caption=caption, is_featured=is_featured)
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
        if photo.image_url and photo.image_url.startswith("/uploads/"):
            filepath = os.path.join(UPLOAD_DIR, os.path.basename(photo.image_url))
            if os.path.exists(filepath):
                os.remove(filepath)
        self.session.delete(photo)
        self.session.commit()
        return {"message": "Photo deleted successfully"}
