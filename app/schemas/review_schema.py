from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ReviewBase(BaseModel):
    user_id: UUID
    destination_id: UUID
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewRead(ReviewBase):
    id: UUID
    created_at: datetime


class ReviewUpdate(BaseModel):
    user_id: Optional[UUID] = None
    destination_id: Optional[UUID] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
