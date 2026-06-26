from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models import EntryCategory


class EntryFeeBase(BaseModel):
    attraction_id: UUID
    category: EntryCategory
    price: Decimal


class EntryFeeCreate(EntryFeeBase):
    pass


class EntryFeeRead(EntryFeeBase):
    id: UUID


class EntryFeeUpdate(BaseModel):
    attraction_id: Optional[UUID] = None
    category: Optional[EntryCategory] = None
    price: Optional[Decimal] = None


class EntryFeeNested(BaseModel):
    category: EntryCategory
    price: Decimal