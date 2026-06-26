from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.route_point_schema import RoutePointNested

from app.models.trekking_route_model import Difficulty


class TrekkingRouteBase(BaseModel):
    destination_id: UUID
    route_name: str
    difficulty: Difficulty
    total_distance_km: Optional[Decimal] = None
    recommended_days: Optional[int] = None
    max_altitude: Optional[int] = None
    description: Optional[str] = None


class TrekkingRouteCreate(TrekkingRouteBase):
    pass


class TrekkingRouteRead(TrekkingRouteBase):
    id: UUID


class TrekkingRouteNested(BaseModel):
    route_name: str
    difficulty: Difficulty
    total_distance_km: Optional[Decimal] = None
    recommended_days: Optional[int] = None
    max_altitude: Optional[int] = None
    description: Optional[str] = None
    route_points: Optional[list[RoutePointNested]] = None


class TrekkingRouteUpdate(BaseModel):
    destination_id: Optional[UUID] = None
    route_name: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    total_distance_km: Optional[Decimal] = None
    recommended_days: Optional[int] = None
    max_altitude: Optional[int] = None
    description: Optional[str] = None
