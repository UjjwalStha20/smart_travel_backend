from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.entry_fee_schema import EntryFeeCreate, EntryFeeNested


class AttractionBase(BaseModel):
    destination_id: UUID
    attraction_types: list
    opening_hours: Optional[str] = Field(default=None, min_length=1)
    visit_duration_hours: Optional[Decimal] = None
    

class AttractionCreate(AttractionBase):
    entry_fee: Optional[EntryFeeCreate] = None


class AttractionRead(AttractionBase):
    id: UUID


class AttractionUpdate(AttractionBase):
    pass


class AttractionNested(BaseModel):
    attraction_types: list
    opening_hours: Optional[str] = Field(default=None, min_length=1)
    visit_duration_hours: Optional[Decimal] = None
    entry_fees: Optional[list["EntryFeeNested"]] = None
