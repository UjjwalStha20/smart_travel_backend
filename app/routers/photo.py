from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import Photo
from app.schemas import PhotoCreate, PhotoUpdate
from app.services import PhotoService

router = APIRouter(prefix="/photos", tags=["Photos"])

class PhotoRouter:

    @router.get("/", response_model=list[Photo], status_code=200)
    async def get_photos(session: SessionDep):
        return PhotoService(session).get_all_photos(offset=0, limit=100)

    @router.get("/{photo_id}", response_model=Photo, status_code=200)
    async def get_photo_by_id(photo_id: str, session: SessionDep):
        return PhotoService(session).get_photo_by_id(photo_id)

    @router.post("/", response_model=Photo, status_code=201)
    async def create_photo(photo_data: PhotoCreate, session: SessionDep):
        return PhotoService(session).create_photo(photo_data)

    @router.put("/{photo_id}", response_model=Photo, status_code=200)
    async def update_photo(photo_id: str, photo_data: PhotoUpdate, session: SessionDep):
        return PhotoService(session).update_photo(photo_id, photo_data)

    @router.delete("/{photo_id}", status_code=200)
    async def delete_photo(photo_id: str, session: SessionDep):
        return PhotoService(session).delete_photo(photo_id)
