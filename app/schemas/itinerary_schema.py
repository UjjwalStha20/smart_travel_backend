from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ItineraryBase(BaseModel):
    trip_id: UUID
    day_number: int
    start_location: str
    end_location: str
    overnight_location: Optional[str] = None
    estimated_walking_hours: Optional[Decimal] = None
    notes: Optional[str] = None


class ItineraryCreate(ItineraryBase):
    pass


class ItineraryRead(ItineraryBase):
    id: UUID


class ItineraryUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    day_number: Optional[int] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    overnight_location: Optional[str] = None
    estimated_walking_hours: Optional[Decimal] = None
    notes: Optional[str] = None
