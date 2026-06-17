from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.attraction_model import AttractionType


class AttractionBase(BaseModel):
    destination_id: UUID
    name: str
    attraction_type: AttractionType
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    visit_duration_hours: Optional[Decimal] = None
    entry_fee: Optional[Decimal] = None
    permit_required: bool = False
    address_id: UUID
    accomodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None


class AttractionCreate(AttractionBase):
    pass


class AttractionRead(AttractionBase):
    id: UUID


class AttractionUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    name: Optional[str] = None
    attraction_type: Optional[AttractionType] = None
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    visit_duration_hours: Optional[Decimal] = None
    entry_fee: Optional[Decimal] = None
    permit_required: Optional[bool] = None
    address_id: Optional[UUID] = None
    accomodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None
