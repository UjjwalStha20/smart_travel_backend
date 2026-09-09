from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models import DestinationCategory
from app.schemas import AddressCreate
from app.schemas.attraction_schema import AttractionNested
from app.schemas.destination_type_detail_schema import (
    HikeDetailsNested,
    MountainDetailsNested,
    NatureDetailsNested,
    TrekDetailsNested,
)
from app.schemas.trekking_route_schema import TrekkingRouteNested


class Month(str, Enum):
    january = "January"
    february = "February"
    march = "March"
    april = "April"
    may = "May"
    june = "June"
    july = "July"
    august = "August"
    september = "September"
    october = "October"
    november = "November"
    december = "December"


class DestinationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: DestinationCategory
    description: str = Field(min_length=1)
    best_time: List[Month]
    permit_required: bool = False
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    highlights: Optional[list] = Field(default_factory=list)

    @field_validator("best_time", mode="before")
    @classmethod
    def normalize_best_time(cls, v):
        if not v:
            raise ValueError("best_time must contain at least one month")
        normalized = [item.strip().title() if isinstance(item, str) else item for item in v]
        if len(normalized) != len(set(normalized)):
            raise ValueError("best_time must not contain duplicate months")
        return normalized

    @field_validator("highlights", mode="before")
    @classmethod
    def normalize_highlights(cls, v):
        if not v:
            return []
        if isinstance(v, str):
            try:
                import json
                v = json.loads(v)
            except Exception:
                v = [v]
        result = [item.strip() for item in v if isinstance(item, str) and item.strip()]
        if not result:
            raise ValueError("highlights must contain at least one short string")
        return result


class DestinationItineraryNested(BaseModel):
    day_number: int = Field(ge=1)
    title: Optional[str] = Field(default=None, min_length=1)
    start_location: str = Field(min_length=1)
    end_location: str = Field(min_length=1)
    overnight_location: Optional[str] = Field(default=None, min_length=1)
    estimated_walking_hours: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, min_length=1)


class DestinationCreate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None
    trek_details: Optional[TrekDetailsNested] = None
    hike_details: Optional[HikeDetailsNested] = None
    mountain_details: Optional[MountainDetailsNested] = None
    nature_details: Optional[NatureDetailsNested] = None
    itinerary: Optional[list[DestinationItineraryNested]] = None


class DestinationRead(DestinationBase):
    id: UUID
    created_at: datetime


class DestinationUpdate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None
    trek_details: Optional[TrekDetailsNested] = None
    hike_details: Optional[HikeDetailsNested] = None
    mountain_details: Optional[MountainDetailsNested] = None
    nature_details: Optional[NatureDetailsNested] = None
    itinerary: Optional[list[DestinationItineraryNested]] = None
    keep_photo_ids: Optional[list[UUID]] = None
    featured_photo_id: Optional[UUID] = None
