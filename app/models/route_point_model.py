from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from fastapi.datastructures import Address
from sqlmodel import Field, Relationship, SQLModel

from app.models.food_cost_model import FoodCost

if TYPE_CHECKING:
    from app.models.accomodation_model import Accommodation
    from app.models.trekking_route_model import TrekkingRoute



# ---------------------------------------------------------------------------
# Route Points
# ---------------------------------------------------------------------------

class RoutePoint(SQLModel, table=True):
    __tablename__ = "route_points"

    id:                          UUID            = Field(default_factory=uuid4, primary_key=True)
    route_id:                    UUID            = Field(foreign_key="trekking_routes.id")
    sequence_no:                 int
    name:                        str
    distance_from_previous_km:   Optional[Decimal] = None
    walking_hours_from_previous: Optional[Decimal] = None
    overnight_stop:              bool              = False
    description:                 Optional[str]     = None
    address_id:                  UUID              = Field(foreign_key="address.id")
    accommodation_id:           Optional[UUID]    = Field(default=None, foreign_key="accommodation.id")
    food_cost_id:              Optional[UUID]    = Field(default=None, foreign_key="food_cost.id")

    # relationships
    route:        "TrekkingRoute" = Relationship(back_populates="route_points")
    accommodation: Optional["Accommodation"] = Relationship(back_populates="route_points")
    food_cost:    Optional["FoodCost"] = Relationship(back_populates="route_points")
    address:      "Address"       = Relationship(back_populates="route_points")
