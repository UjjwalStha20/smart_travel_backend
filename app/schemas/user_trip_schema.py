from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.user_model import BudgetType, PaceType, TripStatus


class UserTripBase(BaseModel):
    user_id: UUID
    destination_id: UUID
    route_id: UUID
    pace_type: PaceType
    budget_type: BudgetType
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: TripStatus = TripStatus.planned


class UserTripCreate(UserTripBase):
    pass


class UserTripRead(UserTripBase):
    id: UUID


class UserTripUpdate(BaseModel):
    user_id: Optional[UUID] = None
    destination_id: Optional[UUID] = None
    route_id: Optional[UUID] = None
    pace_type: Optional[PaceType] = None
    budget_type: Optional[BudgetType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TripStatus] = None
