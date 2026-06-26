from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.entry_fee_model import EntryFee

if TYPE_CHECKING:
    from app.models import Accommodation, FoodCost, Destination , EntryFee


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
    attraction_type:      AttractionType
    opening_hours:        Optional[str]     = None
    visit_duration_hours: Optional[Decimal] = None


    # relationships
    destination:  "Destination"   = Relationship(back_populates="attractions")
    accommodations: list["Accommodation"] = Relationship(back_populates="attractions")
    food_costs:    list["FoodCost"] = Relationship(back_populates="attractions")
    entry_fees:   list["EntryFee"] = Relationship(back_populates="attraction")
