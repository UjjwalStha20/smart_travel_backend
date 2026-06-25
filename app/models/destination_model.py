from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel, Text

if TYPE_CHECKING:
    from app.models.attraction_model import Attraction
    from app.models.permit_model import Permit
    from app.models.photo_model import Photo
    from app.models.review_model import Review
    from app.models.trekking_route_model import TrekkingRoute
    from app.models.user_model import SavedDestination, UserTrip



class DestinationCategory(str, Enum):
    attraction = "attraction"
    trek     = "trek"

# ---------------------------------------------------------------------------
# Destination
# ---------------------------------------------------------------------------

class Destination(SQLModel, table=True):
    __tablename__ = "destination"

    id:              UUID                    = Field(default_factory=uuid4, primary_key=True)
    name:            str
    category:        DestinationCategory
    description:     str                     = Field(sa_type=Text)        
    best_time:       list                    = Field(default=None, sa_type=JSON)
    permit_required: bool                    = False
    rating:          Optional[int]           = None
    created_at:      datetime                = Field(default_factory=datetime.utcnow)
    address_id:      UUID                    = Field(foreign_key="address.id")

    # relationships
    attractions:        List["Attraction"]       = Relationship(back_populates="destination")
    trekking_routes:    List["TrekkingRoute"]    = Relationship(back_populates="destination")
    permits:            List["Permit"]           = Relationship(back_populates="destination")
    photos:             List["Photo"]            = Relationship(back_populates="destination")
    reviews:            List["Review"]           = Relationship(back_populates="destination")
    saved_destinations: List["SavedDestination"] = Relationship(back_populates="destination")
    user_trips:         List["UserTrip"]         = Relationship(back_populates="destination")

