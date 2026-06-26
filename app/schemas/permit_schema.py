from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.permit_model import PermitCategory


class PermitBase(BaseModel):
    destination_id: UUID
    category: PermitCategory
    price: Decimal


class PermitCreate(PermitBase):
    pass


class PermitRead(PermitBase):
    id: UUID


class PermitUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    category: Optional[PermitCategory] = None
    price: Optional[Decimal] = None
