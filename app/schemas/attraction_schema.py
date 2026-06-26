from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models import AttractionType 
from app.schemas import EntryFeeCreate


class AttractionBase(BaseModel):
    destination_id: UUID
    attraction_type: AttractionType
    opening_hours: Optional[str] = None
    visit_duration_hours: Optional[Decimal] = None
    

class AttractionCreate(AttractionBase):
    entry_fee: EntryFeeCreate | None = None


class AttractionRead(AttractionBase):
    id: UUID


class AttractionUpdate(AttractionBase):
    pass
