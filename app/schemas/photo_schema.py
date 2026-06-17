from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PhotoBase(BaseModel):
    destination_id: UUID
    uploaded_by: UUID
    image_url: str
    caption: Optional[str] = None


class PhotoCreate(PhotoBase):
    pass


class PhotoRead(PhotoBase):
    id: UUID


class PhotoUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    image_url: Optional[str] = None
    caption: Optional[str] = None
