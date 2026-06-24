from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccommodationBase(BaseModel):
    budget_price: Decimal
    standard_price: Optional[Decimal] = None
    luxury_price: Optional[Decimal] = None


class AccommodationCreate(AccommodationBase):
    pass


class AccommodationRead(AccommodationBase):
    id: UUID


class AccommodationUpdate(BaseModel):
    budget_price: Optional[Decimal] = None
    standard_price: Optional[Decimal] = None
    luxury_price: Optional[Decimal] = None
