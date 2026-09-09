from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FoodCostBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the food item (e.g., Dal Bhat, Momos)")
    category: Optional[str] = Field(default=None, max_length=50, description="Category of the food (e.g., Main Meal, Drink, Snack)")
    
    budget_price: Decimal = Field(ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))


class FoodCostCreate(FoodCostBase):
    pass


class FoodCostRead(FoodCostBase):
    id: UUID


class FoodCostUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    budget_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    standard_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    luxury_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))