from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import DestinationCategory
from app.schemas import AddressCreate
from app.schemas.attraction_schema import AttractionNested
from app.schemas.trekking_route_schema import TrekkingRouteNested

class DestinationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: DestinationCategory
    description: str = Field(min_length=1)
    best_time: List
    permit_required: bool = False
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    


class DestinationCreate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None


class DestinationRead(DestinationBase):
    id: UUID
    created_at: datetime


class DestinationUpdate(DestinationBase):
    address: AddressCreate
