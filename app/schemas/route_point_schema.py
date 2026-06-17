from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RoutePointBase(BaseModel):
    route_id: UUID
    sequence_no: int
    name: str
    distance_from_previous_km: Optional[Decimal] = None
    walking_hours_from_previous: Optional[Decimal] = None
    overnight_stop: bool = False
    description: Optional[str] = None
    address_id: UUID
    accommodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None


class RoutePointCreate(RoutePointBase):
    pass


class RoutePointRead(RoutePointBase):
    id: UUID


class RoutePointUpdate(BaseModel):
    route_id: Optional[UUID] = None
    sequence_no: Optional[int] = None
    name: Optional[str] = None
    distance_from_previous_km: Optional[Decimal] = None
    walking_hours_from_previous: Optional[Decimal] = None
    overnight_stop: Optional[bool] = None
    description: Optional[str] = None
    address_id: Optional[UUID] = None
    accommodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None
