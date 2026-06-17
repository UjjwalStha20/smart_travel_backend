from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.accomodation_model import Accommodation
    from app.models.address_model import Address
    from app.models.destination_model import Destination
    from app.models.food_cost_model import FoodCost

class AttractionType(str, Enum):
    temple    = "temple"
    heritage  = "heritage"
    hiking    = "hiking"
    lake      = "lake"
    viewpoint = "viewpoint"


# ---------------------------------------------------------------------------
# Attraction
# ---------------------------------------------------------------------------

class Attraction(SQLModel, table=True):
    __tablename__ = "attraction"

    id:                   UUID              = Field(default_factory=uuid4, primary_key=True)
    destination_id:       UUID              = Field(foreign_key="destination.id")
    name:                 str
    attraction_type:      AttractionType
    description:          Optional[str]     = None
    opening_hours:        Optional[str]     = None
    visit_duration_hours: Optional[Decimal] = None
    entry_fee:            Optional[Decimal] = None
    permit_required:      bool              = False
    address_id:          UUID              = Field(foreign_key="address.id") 
    accomodation_id:     Optional[UUID]    = Field(default=None, foreign_key="accommodation.id")
    food_cost_id:        Optional[UUID]    = Field(default=None, foreign_key="food_cost.id")

    # relationships
    destination:  "Destination"   = Relationship(back_populates="attractions")
    accommodation: Optional["Accommodation"] = Relationship(back_populates="attractions")
    food_cost:    Optional["FoodCost"] = Relationship(back_populates="attractions")
    address:      "Address"       = Relationship(back_populates="attractions")

