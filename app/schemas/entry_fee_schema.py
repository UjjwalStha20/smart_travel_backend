from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models import EntryCategory


class EntryFeeBase(BaseModel):
    destination_id: UUID
    category: EntryCategory
    price: Decimal


class EntryFeeCreate(EntryFeeBase):
    pass


class EntryFeeRead(EntryFeeBase):
    id: UUID


class EntryFeeUpdate(EntryFeeBase):
    price: Decimal | None = None