from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Attraction, RoutePoint

# ---------------------------------------------------------------------------
# Food Cost
# ---------------------------------------------------------------------------

class FoodCost(SQLModel, table=True):
    __tablename__ = "food_cost"

    id:             UUID              = Field(default_factory=uuid4, primary_key=True)
    name:           str               = Field(default="")  # <-- ADDED (e.g., "Dal Bhat", "Garlic Soup")
    category:       Optional[str]     = None               # <-- ADDED (e.g., "Main Meal", "Drink", "Snack")
    
    budget_price:   Decimal           = Field(default=None)
    standard_price: Optional[Decimal] = None
    luxury_price:   Optional[Decimal] = None

    # relationships
    route_points: List["RoutePoint"] = Relationship(back_populates="food_cost")