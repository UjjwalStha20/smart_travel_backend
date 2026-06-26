from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import JSON

from app.models.entry_fee_model import EntryFee

if TYPE_CHECKING:
    from app.models import Destination , EntryFee


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
    destination_id:       UUID              = Field(foreign_key="destination.id", unique=True)
    attraction_types:     Optional[list]    = Field(default=None, sa_type=JSON)
    opening_hours:        Optional[str]     = None
    visit_duration_hours: Optional[Decimal] = None


    # relationships
    destination:  "Destination"   = Relationship(back_populates="attraction")
    entry_fees:   list["EntryFee"] = Relationship(back_populates="attraction")
