from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Destination , RoutePoint, UserTrip
    

class Difficulty(str, Enum):
    easy     = "easy"
    moderate = "moderate"
    hard     = "hard"


# ---------------------------------------------------------------------------
# Trekking Routes
# ---------------------------------------------------------------------------

class TrekkingRoute(SQLModel, table=True):
    __tablename__ = "trekking_routes"

    id:                UUID            = Field(default_factory=uuid4, primary_key=True)
    destination_id:    UUID            = Field(foreign_key="destination.id")
    route_name:        str
    difficulty:        Difficulty
    total_distance_km: Optional[Decimal] = None
    recommended_days:  Optional[int]    = None
    max_altitude:      Optional[int]    = None
    description:       Optional[str]   = None

    # relationships
    destination:  "Destination"    = Relationship(back_populates="trekking_routes")
    route_points: List["RoutePoint"] = Relationship(back_populates="route")
    user_trips:   List["UserTrip"]  = Relationship(back_populates="route")
