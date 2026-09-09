from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel, Text

if TYPE_CHECKING:
    from app.models import (
        Attraction, Permit, Photo, Review, TrekkingRoute, SavedDestination,
        UserTrip, Address, DestinationItinerary, DestinationHighlight,
        DestinationThingToDo, DestinationFaq, TrekDetails, HikeDetails,
        MountainDetails, NatureDetails,
    )


class DestinationCategory(str, Enum):
    attraction    = "attraction"
    trek          = "trek"
    hike          = "hike"
    mountain      = "mountain"
    nature        = "nature"
    lake          = "lake"
    waterfall     = "waterfall"
    viewpoint     = "viewpoint"
    city          = "city"
    cultural_site = "cultural_site"
    religious_site = "religious_site"
    historical_site = "historical_site"
    wildlife      = "wildlife"
    adventure     = "adventure"
    other         = "other"

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
    highlights:      list                    = Field(default=None, sa_type=JSON)
    created_at:      datetime                = Field(default_factory=datetime.utcnow)
    address_id:      UUID                    = Field(foreign_key="address.id")

    # relationships
    attraction:         Optional["Attraction"]   = Relationship(back_populates="destination")
    trekking_routes:    List["TrekkingRoute"]    = Relationship(back_populates="destination")
    permits:            List["Permit"]           = Relationship(back_populates="destination")
    photos:             List["Photo"]            = Relationship(back_populates="destination")
    reviews:            List["Review"]           = Relationship(back_populates="destination")
    saved_destinations: List["SavedDestination"] = Relationship(back_populates="destination")
    user_trips:              List["UserTrip"]              = Relationship(back_populates="destination")
    destination_itineraries: List["DestinationItinerary"]  = Relationship(back_populates="destination")
    address:                 "Address"                     = Relationship(back_populates="destinations")
    content_highlights:      List["DestinationHighlight"]  = Relationship(back_populates="destination")
    things_to_do:            List["DestinationThingToDo"]  = Relationship(back_populates="destination")
    faqs:                    List["DestinationFaq"]        = Relationship(back_populates="destination")
    trek_details:            Optional["TrekDetails"]       = Relationship(back_populates="destination")
    hike_details:            Optional["HikeDetails"]       = Relationship(back_populates="destination")
    mountain_details:        Optional["MountainDetails"]   = Relationship(back_populates="destination")
    nature_details:          Optional["NatureDetails"]     = Relationship(back_populates="destination")

