from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel, Text

from app.models.trekking_route_model import Difficulty

if TYPE_CHECKING:
    from app.models import Destination


class AccommodationType(str, Enum):
    tea_house = "tea_house"
    lodge       = "lodge"
    camping     = "camping"
    mixed       = "mixed"


# ---------------------------------------------------------------------------
# Type-specific detail rows (one-to-one with destination)
# ---------------------------------------------------------------------------


class TrekDetails(SQLModel, table=True):
    __tablename__ = "trek_details"

    id:                   UUID               = Field(default_factory=uuid4, primary_key=True)
    destination_id:       UUID               = Field(foreign_key="destination.id", unique=True, index=True)
    duration_days:        Optional[int]      = Field(default=None, ge=1)
    distance_km:          Optional[Decimal]  = Field(default=None, ge=0)
    max_elevation:        Optional[Decimal]  = Field(default=None, ge=0)
    elevation_gain:       Optional[Decimal]  = Field(default=None, ge=0)
    difficulty:           Optional[Difficulty] = None
    best_season:          Optional[str]      = None
    start_point:          Optional[str]      = None
    end_point:            Optional[str]      = None
    required_permits:     Optional[str]      = None
    guide_required:       bool               = False
    guide_recommended:    bool               = False
    accommodation_type:   Optional[AccommodationType] = None

    destination: "Destination" = Relationship(back_populates="trek_details")


class HikeDetails(SQLModel, table=True):
    __tablename__ = "hike_details"

    id:                     UUID              = Field(default_factory=uuid4, primary_key=True)
    destination_id:         UUID              = Field(foreign_key="destination.id", unique=True, index=True)
    difficulty:             Optional[Difficulty] = None
    duration_hours:         Optional[Decimal] = Field(default=None, ge=0)
    distance_km:            Optional[Decimal] = Field(default=None, ge=0)
    elevation_gain:         Optional[Decimal] = Field(default=None, ge=0)
    highest_elevation:      Optional[Decimal] = Field(default=None, ge=0)
    starting_point:         Optional[str]     = None
    ending_point:           Optional[str]     = None
    estimated_hiking_time:  Optional[str]     = None
    guide_recommended:      bool              = False
    required_permits:       Optional[str]     = None
    trail_type:             Optional[str]     = None
    water_availability:     Optional[str]     = None
    accommodation_available: Optional[str]    = None
    route_description:      Optional[str]     = Field(default=None, sa_type=Text)

    destination: "Destination" = Relationship(back_populates="hike_details")


class MountainDetails(SQLModel, table=True):
    __tablename__ = "mountain_details"

    id:                        UUID              = Field(default_factory=uuid4, primary_key=True)
    destination_id:            UUID              = Field(foreign_key="destination.id", unique=True, index=True)
    elevation:                 Optional[Decimal] = Field(default=None, ge=0)
    difficulty:                Optional[Difficulty] = None
    climbing_season:           Optional[str]     = None
    required_permits:          Optional[str]     = None
    expedition_required:       bool              = False
    base_camp:                 Optional[str]     = None
    technical_climbing_required: bool            = False
    approx_duration:           Optional[str]     = None
    guide_required:            bool              = False

    destination: "Destination" = Relationship(back_populates="mountain_details")


class NatureDetails(SQLModel, table=True):
    __tablename__ = "nature_details"

    id:                                UUID              = Field(default_factory=uuid4, primary_key=True)
    destination_id:                    UUID              = Field(foreign_key="destination.id", unique=True, index=True)
    visit_duration_hours:              Optional[Decimal] = Field(default=None, ge=0)
    opening_hours:                     Optional[str]     = None
    difficulty_if_hiking:              Optional[Difficulty] = None
    distance_from_nearest_major_location: Optional[str]  = None
    accessibility:                     Optional[str]     = None
    best_viewing_season:               Optional[str]     = None
    activities:                        Optional[list]    = Field(default=None, sa_type=JSON)
    safety_considerations:             Optional[str]     = Field(default=None, sa_type=Text)

    destination: "Destination" = Relationship(back_populates="nature_details")