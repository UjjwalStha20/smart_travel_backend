from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SavedDestinationBase(BaseModel):
    user_id: UUID
    destination_id: UUID


class SavedDestinationCreate(BaseModel):
    destination_id: UUID


class SavedDestinationRead(SavedDestinationBase):
    id: UUID
    created_at: datetime


class SavedDestinationUpdate(BaseModel):
    user_id: Optional[UUID] = None
    destination_id: Optional[UUID] = None
