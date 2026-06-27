from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Destination


class DestinationItinerary(SQLModel, table=True):
    __tablename__ = "destination_itinerary"

    id:                      UUID            = Field(default_factory=uuid4, primary_key=True)
    destination_id:          UUID            = Field(foreign_key="destination.id")
    day_number:              int
    title:                   Optional[str]   = None
    start_location:          str
    end_location:            str
    overnight_location:      Optional[str]   = None
    estimated_walking_hours: Optional[Decimal] = None
    notes:                   Optional[str]   = None

    # relationships
    destination: "Destination" = Relationship(back_populates="destination_itineraries")
