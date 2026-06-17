from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.destination_model import DestinationCategory
from app.schemas.address_schema import AddressCreate

class DestinationBase(BaseModel):
    name: str
    category: DestinationCategory
    description: str 
    best_time: List
    permit_required: bool = False
    rating: Optional[int] = None
    


class DestinationCreate(DestinationBase):
    address: AddressCreate


class DestinationRead(DestinationBase):
    id: UUID
    created_at: datetime


class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[DestinationCategory] = None
    description: Optional[str] = None
    best_time: Optional[list] = None
    permit_required: Optional[bool] = None
    rating: Optional[int] = None
    address_id: Optional[UUID] = None
