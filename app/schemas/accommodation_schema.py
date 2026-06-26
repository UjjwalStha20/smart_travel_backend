from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AccommodationBase(BaseModel):
    budget_price: Decimal = Field(ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class AccommodationCreate(AccommodationBase):
    pass


class AccommodationRead(AccommodationBase):
    id: UUID


class AccommodationUpdate(BaseModel):
    budget_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
