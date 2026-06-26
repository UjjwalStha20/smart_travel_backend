from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    user_id: UUID
    destination_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewCreate(BaseModel):
    destination_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewRead(ReviewBase):
    id: UUID
    created_at: datetime


class ReviewUpdate(BaseModel):
    user_id: Optional[UUID] = None
    destination_id: Optional[UUID] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)
