from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FoodCostBase(BaseModel):
    budget_price: Decimal = Field(ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class FoodCostCreate(FoodCostBase):
    pass


class FoodCostRead(FoodCostBase):
    id: UUID


class FoodCostUpdate(BaseModel):
    budget_price: Decimal = Field(ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
