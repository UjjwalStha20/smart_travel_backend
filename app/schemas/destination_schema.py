from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models import DestinationCategory
from app.schemas import AddressCreate
from app.schemas.attraction_schema import AttractionNested
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

    @field_validator("best_time", mode="before")
    @classmethod
    def normalize_best_time(cls, v):
        if not v:
            raise ValueError("best_time must contain at least one month")
        normalized = [item.strip().title() if isinstance(item, str) else item for item in v]
        if len(normalized) != len(set(normalized)):
            raise ValueError("best_time must not contain duplicate months")
        return normalized
    


class DestinationCreate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None


class DestinationRead(DestinationBase):
    id: UUID
    created_at: datetime


class DestinationUpdate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None
    keep_photo_ids: Optional[list[UUID]] = None
