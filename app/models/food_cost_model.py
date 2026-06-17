from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel



if TYPE_CHECKING:
    from app.models.attraction_model import Attraction
    from app.models.route_point_model import RoutePoint




# ---------------------------------------------------------------------------
# Food Cost
# ---------------------------------------------------------------------------

class FoodCost(SQLModel, table=True):
    __tablename__ = "food_cost"

    id:             UUID              = Field(default_factory=uuid4, primary_key=True)
    budget_price:   Decimal           = Field(default=None)
    standard_price: Optional[Decimal] = None
    luxury_price:   Optional[Decimal] = None

    # relationships
    attractions: List["Attraction"] = Relationship(back_populates="food_cost")
    route_points: List["RoutePoint"] = Relationship(back_populates="food_cost")


