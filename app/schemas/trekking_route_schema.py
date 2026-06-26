from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.route_point_schema import RoutePointNested

from app.models.trekking_route_model import Difficulty


class TrekkingRouteBase(BaseModel):
    destination_id: UUID
    route_name: str = Field(min_length=1)
    difficulty: Difficulty
    total_distance_km: Optional[Decimal] = Field(default=None, ge=0)
    recommended_days: Optional[int] = Field(default=None, ge=1)
    max_altitude: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, min_length=1)


class TrekkingRouteCreate(TrekkingRouteBase):
    pass


class TrekkingRouteRead(TrekkingRouteBase):
    id: UUID


class TrekkingRouteNested(BaseModel):
    route_name: str = Field(min_length=1)
    difficulty: Difficulty
    total_distance_km: Optional[Decimal] = Field(default=None, ge=0)
    recommended_days: Optional[int] = Field(default=None, ge=1)
    max_altitude: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, min_length=1)
    route_points: Optional[list[RoutePointNested]] = None


class TrekkingRouteUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    route_name: Optional[str] = Field(default=None, min_length=1)
    difficulty: Optional[Difficulty] = None
    total_distance_km: Optional[Decimal] = Field(default=None, ge=0)
    recommended_days: Optional[int] = Field(default=None, ge=1)
    max_altitude: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, min_length=1)
