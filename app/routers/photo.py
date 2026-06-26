from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.dependencies import CurrentUser, SessionDep
from app.models import Photo
from app.schemas import PhotoCreate, PhotoUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import PhotoService

router = APIRouter(prefix="/photos", tags=["Photos"])

class PhotoRouter:

    @router.get("/", response_model=PaginatedResponse[Photo], status_code=200)
    async def get_photos(session: SessionDep):
        return PhotoService(session).get_all_photos(offset=0, limit=100)

    @router.get("/{photo_id}", response_model=Photo, status_code=200)
    async def get_photo_by_id(photo_id: str, session: SessionDep):
        return PhotoService(session).get_photo_by_id(photo_id)

    @router.post("/", response_model=Photo, status_code=201)
    async def create_photo(
        destination_id: UUID = Form(...),
        file: UploadFile = File(...),
        caption: str | None = Form(None),
        session: SessionDep = None,
        current_user: CurrentUser = None,
    ):
        content = await file.read()
        return PhotoService(session).create_photo_from_upload(destination_id, current_user.id, file.filename or "photo.jpg", content, caption)

    @router.post("/json", response_model=Photo, status_code=201)
    async def create_photo_json(photo_data: PhotoCreate, session: SessionDep, current_user: CurrentUser):
        data = photo_data.model_dump() | {"uploaded_by": current_user.id}
        return PhotoService(session).create_photo(data)

    @router.put("/{photo_id}", response_model=Photo, status_code=200)
    async def update_photo(photo_id: str, photo_data: PhotoUpdate, session: SessionDep, current_user: CurrentUser):
        existing = PhotoService(session).get_photo_by_id(photo_id)
        if existing.uploaded_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your photo")
        return PhotoService(session).update_photo(photo_id, photo_data)

    @router.delete("/{photo_id}", status_code=200)
    async def delete_photo(photo_id: str, session: SessionDep, current_user: CurrentUser):
        existing = PhotoService(session).get_photo_by_id(photo_id)
        if existing.uploaded_by != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your photo")
        return PhotoService(session).delete_photo(photo_id)
