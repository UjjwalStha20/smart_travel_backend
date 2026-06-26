from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models import DestinationCategory
from app.schemas import AddressCreate
from app.schemas.attraction_schema import AttractionNested
from app.schemas.trekking_route_schema import TrekkingRouteNested

class DestinationBase(BaseModel):
    name: str
    category: DestinationCategory
    description: str 
    best_time: List
    permit_required: bool = False
    rating: Optional[int] = None
    


class DestinationCreate(DestinationBase):
    address: AddressCreate
    attraction: Optional[AttractionNested] = None
    trekking_routes: Optional[list[TrekkingRouteNested]] = None


class DestinationRead(DestinationBase):
    id: UUID
    created_at: datetime


class DestinationUpdate(DestinationBase):
    address: AddressCreate
