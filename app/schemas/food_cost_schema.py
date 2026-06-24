from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class FoodCostBase(BaseModel):
    budget_price: Decimal
    standard_price: Optional[Decimal] = None
    luxury_price: Optional[Decimal] = None


class FoodCostCreate(FoodCostBase):
    pass


class FoodCostRead(FoodCostBase):
    id: UUID


class FoodCostUpdate(BaseModel):
    budget_price: Decimal
    standard_price: Optional[Decimal] = None
    luxury_price: Optional[Decimal] = None
