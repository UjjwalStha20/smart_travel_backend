from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PhotoBase(BaseModel):
    destination_id: UUID
    uploaded_by: UUID
    image_url: str = Field(min_length=1)
    caption: Optional[str] = None


class PhotoCreate(BaseModel):
    destination_id: UUID
    image_url: Optional[str] = Field(default=None, min_length=1)
    caption: Optional[str] = Field(default=None, max_length=500)


class PhotoRead(PhotoBase):
    id: UUID


class PhotoUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    image_url: Optional[str] = Field(default=None, min_length=1)
    caption: Optional[str] = None
