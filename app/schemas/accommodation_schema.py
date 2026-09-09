from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AccommodationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the teahouse/lodge")
    description: Optional[str] = Field(default=None, max_length=500, description="Short description of the accommodation")
    location: Optional[str] = Field(default=None, max_length=200, description="Location of the accommodation")
    budget_price: Decimal = Field(ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class AccommodationCreate(AccommodationBase):
    pass


class AccommodationRead(AccommodationBase):
    id: UUID


class AccommodationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=200)
    budget_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))