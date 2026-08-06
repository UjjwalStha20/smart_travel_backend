from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import UniqueConstraint
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import Blog, ChatConversation, Destination , Photo , Review, TrekkingRoute
   
class UserRole(str, Enum):
    traveler = "traveler"
    guide    = "guide"
    admin    = "admin"

class PaceType(str, Enum):
    slow   = "slow"
    normal = "normal"
    fast   = "fast"

class BudgetType(str, Enum):
    budget   = "budget"
    standard = "standard"
    luxury   = "luxury"


class TripStatus(str, Enum):
    planned   = "planned"
    ongoing   = "ongoing"
    completed = "completed"
    

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    role: UserRole
    nationality: Optional[str] = None
    email: EmailStr = Field(unique=True)
    password: str
    phone: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc) ,sa_column=Column(DateTime(timezone=True)))
 
    # ✅ relationships (correct SQLModel way)
    photos: List["Photo"] = Relationship(back_populates="uploader")
    reviews: List["Review"] = Relationship(back_populates="user")
    trips: List["UserTrip"] = Relationship(back_populates="user")
    saved_destinations: List["SavedDestination"] = Relationship(back_populates="user")
    chat_conversations: List["ChatConversation"] = Relationship(back_populates="user")
    blogs: List["Blog"] = Relationship(back_populates="author")


# ---------------------------------------------------------------------------
# User Trips
# ---------------------------------------------------------------------------

class UserTrip(SQLModel, table=True):
    __tablename__ = "user_trips"

    id:             UUID          = Field(default_factory=uuid4, primary_key=True)
    user_id:        UUID          = Field(foreign_key="users.id")
    destination_id: UUID          = Field(foreign_key="destination.id")
    route_id:       UUID          = Field(foreign_key="trekking_routes.id")
    pace_type:      PaceType
    budget_type:    BudgetType
    start_date:     Optional[date] = None
    end_date:       Optional[date] = None
    status:         TripStatus     = TripStatus.planned

    # relationships
    user:        "User"            = Relationship(back_populates="trips")
    destination: "Destination"     = Relationship(back_populates="user_trips")
    route:       "TrekkingRoute"   = Relationship(back_populates="user_trips")
    itineraries: List["Itinerary"] = Relationship(back_populates="trip")


# ---------------------------------------------------------------------------
# Itinerary
# ---------------------------------------------------------------------------

class Itinerary(SQLModel, table=True):
    __tablename__ = "itinerary"

    id:                      UUID          = Field(default_factory=uuid4, primary_key=True)
    trip_id:                 UUID          = Field(foreign_key="user_trips.id")
    day_number:              int
    start_location:          str
    end_location:            str
    overnight_location:      Optional[str]     = None
    estimated_walking_hours: Optional[Decimal] = None
    notes:                   Optional[str]     = None

    # relationships
    trip: "UserTrip" = Relationship(back_populates="itineraries")


# ---------------------------------------------------------------------------
# Saved Destinations
# ---------------------------------------------------------------------------

class SavedDestination(SQLModel, table=True):
    __tablename__ = "saved_destinations"
    __table_args__ = (UniqueConstraint("user_id", "destination_id"),)

    id:             UUID     = Field(default_factory=uuid4, primary_key=True)
    user_id:        UUID     = Field(foreign_key="users.id")
    destination_id: UUID     = Field(foreign_key="destination.id")
    created_at:     datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # relationships
    user:        "User"        = Relationship(back_populates="saved_destinations")
    destination: "Destination" = Relationship(back_populates="saved_destinations")