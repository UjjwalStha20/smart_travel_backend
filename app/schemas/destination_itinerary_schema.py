from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DestinationItineraryBase(BaseModel):
    destination_id: UUID
    day_number: int = Field(ge=1)
    title: Optional[str] = Field(default=None, min_length=1)
    start_location: str = Field(min_length=1)
    end_location: str = Field(min_length=1)
    overnight_location: Optional[str] = Field(default=None, min_length=1)
    estimated_walking_hours: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, min_length=1)


class DestinationItineraryCreate(DestinationItineraryBase):
    pass


class DestinationItineraryRead(DestinationItineraryBase):
    id: UUID


class DestinationItineraryUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    day_number: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, min_length=1)
    start_location: Optional[str] = Field(default=None, min_length=1)
    end_location: Optional[str] = Field(default=None, min_length=1)
    overnight_location: Optional[str] = Field(default=None, min_length=1)
    estimated_walking_hours: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, min_length=1)
