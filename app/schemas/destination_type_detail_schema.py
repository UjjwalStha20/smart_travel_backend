from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.destination_type_detail_model import AccommodationType
from app.models.trekking_route_model import Difficulty


class TrekDetailsNested(BaseModel):
    duration_days:        Optional[int]               = Field(default=None, ge=1)
    distance_km:          Optional[Decimal]           = Field(default=None, ge=0)
    max_elevation:        Optional[Decimal]           = Field(default=None, ge=0)
    elevation_gain:       Optional[Decimal]           = Field(default=None, ge=0)
    difficulty:           Optional[Difficulty]        = None
    best_season:          Optional[str]               = Field(default=None, min_length=1)
    start_point:          Optional[str]               = Field(default=None, min_length=1)
    end_point:            Optional[str]               = Field(default=None, min_length=1)
    required_permits:     Optional[str]               = Field(default=None, min_length=1)
    guide_required:       bool                        = False
    guide_recommended:    bool                        = False
    accommodation_type:   Optional[AccommodationType] = None


class HikeDetailsNested(BaseModel):
    difficulty:               Optional[Difficulty] = None
    duration_hours:           Optional[Decimal]    = Field(default=None, ge=0)
    distance_km:              Optional[Decimal]    = Field(default=None, ge=0)
    elevation_gain:           Optional[Decimal]    = Field(default=None, ge=0)
    highest_elevation:        Optional[Decimal]    = Field(default=None, ge=0)
    starting_point:           Optional[str]        = Field(default=None, min_length=1)
    ending_point:             Optional[str]        = Field(default=None, min_length=1)
    estimated_hiking_time:    Optional[str]        = Field(default=None, min_length=1)
    guide_recommended:        bool                 = False
    required_permits:         Optional[str]        = Field(default=None, min_length=1)
    trail_type:               Optional[str]        = Field(default=None, min_length=1)
    water_availability:       Optional[str]        = Field(default=None, min_length=1)
    accommodation_available:  Optional[str]        = Field(default=None, min_length=1)
    route_description:        Optional[str]        = Field(default=None, min_length=1)


class MountainDetailsNested(BaseModel):
    elevation:                    Optional[Decimal] = Field(default=None, ge=0)
    difficulty:                   Optional[Difficulty] = None
    climbing_season:              Optional[str]     = Field(default=None, min_length=1)
    required_permits:             Optional[str]     = Field(default=None, min_length=1)
    expedition_required:          bool              = False
    base_camp:                    Optional[str]     = Field(default=None, min_length=1)
    technical_climbing_required:  bool              = False
    approx_duration:              Optional[str]     = Field(default=None, min_length=1)
    guide_required:               bool              = False


class NatureDetailsNested(BaseModel):
    visit_duration_hours:                 Optional[Decimal] = Field(default=None, ge=0)
    opening_hours:                        Optional[str]     = Field(default=None, min_length=1)
    difficulty_if_hiking:                 Optional[Difficulty] = None
    distance_from_nearest_major_location: Optional[str]     = Field(default=None, min_length=1)
    accessibility:                        Optional[str]     = Field(default=None, min_length=1)
    best_viewing_season:                  Optional[str]     = Field(default=None, min_length=1)
    activities:                           Optional[list]    = None
    safety_considerations:                Optional[str]     = Field(default=None, min_length=1)