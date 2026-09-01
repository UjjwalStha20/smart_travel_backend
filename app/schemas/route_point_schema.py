from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.address_schema import AddressCreate


class RoutePointBase(BaseModel):
    route_id: UUID
    sequence_no: int = Field(ge=1)
    name: str = Field(min_length=1)
    distance_from_previous_km: Optional[Decimal] = Field(default=None, ge=0)
    walking_hours_from_previous: Optional[Decimal] = Field(default=None, ge=0)
    overnight_stop: bool = False
    description: Optional[str] = Field(default=None, min_length=1)
    address_id: UUID
    accommodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None


class RoutePointCreate(RoutePointBase):
    pass


class RoutePointRead(RoutePointBase):
    id: UUID


class RoutePointNested(BaseModel):
    sequence_no: int = Field(ge=1)
    name: str = Field(min_length=1)
    distance_from_previous_km: Optional[Decimal] = Field(default=None, ge=0)
    walking_hours_from_previous: Optional[Decimal] = Field(default=None, ge=0)
    overnight_stop: bool = False
    description: Optional[str] = Field(default=None, min_length=1)
    address: Optional[AddressCreate] = None
    address_id: Optional[UUID] = None
    accommodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None

    @model_validator(mode="after")
    def check_address(self):
        if self.address is None and self.address_id is None:
            raise ValueError("Route point requires an address or address_id")
        return self


class RoutePointUpdate(BaseModel):
    route_id: Optional[UUID] = None
    sequence_no: Optional[int] = Field(default=None, ge=1)
    name: Optional[str] = Field(default=None, min_length=1)
    distance_from_previous_km: Optional[Decimal] = Field(default=None, ge=0)
    walking_hours_from_previous: Optional[Decimal] = Field(default=None, ge=0)
    overnight_stop: Optional[bool] = None
    description: Optional[str] = Field(default=None, min_length=1)
    address_id: Optional[UUID] = None
    accommodation_id: Optional[UUID] = None
    food_cost_id: Optional[UUID] = None
