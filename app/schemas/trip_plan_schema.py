from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.trip_plan_model import TripDaySource, TripPlanStatus


class TripPlanBase(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    destinations: List[str] = Field(default_factory=list)
    start_location: Optional[str] = None
    travelers: Dict = Field(default_factory=dict)
    budget: Dict = Field(default_factory=dict)
    trip_types: List[str] = Field(default_factory=list)
    transportation: List[str] = Field(default_factory=list)
    accommodation: Optional[str] = None
    preferences: Dict = Field(default_factory=dict)
    special_requirements: Dict = Field(default_factory=dict)


class TripPlanCreate(TripPlanBase):
    pass


class TripPlanUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TripPlanStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    destinations: Optional[List[str]] = None
    start_location: Optional[str] = None
    travelers: Optional[Dict] = None
    budget: Optional[Dict] = None
    trip_types: Optional[List[str]] = None
    transportation: Optional[List[str]] = None
    accommodation: Optional[str] = None
    preferences: Optional[Dict] = None
    special_requirements: Optional[Dict] = None
    summary: Optional[str] = None


class TripPreferenceUpdate(BaseModel):
    answers: Dict = Field(default_factory=dict)


class TripItineraryItemOut(BaseModel):
    id: UUID
    position: int
    title: str
    category: Optional[str] = None
    location: Optional[str] = None
    duration_hours: Optional[float] = None
    notes: Optional[str] = None
    recommendation_id: Optional[UUID] = None


class TripItineraryDayOut(BaseModel):
    id: UUID
    day_number: int
    date: Optional[date] = None
    location: Optional[str] = None
    title: Optional[str] = None
    transportation: List[str] = Field(default_factory=list)
    estimated_duration_hours: Optional[float] = None
    notes: Optional[str] = None
    status: TripDaySource
    items: List[TripItineraryItemOut] = Field(default_factory=list)


class TripMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    intent: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime


class TripEditOut(BaseModel):
    id: UUID
    field: str
    new_value: str
    origin: str
    message_id: Optional[UUID] = None
    created_at: datetime


class TripRecommendationOut(BaseModel):
    id: UUID
    kind: str
    destination_id: Optional[UUID] = None
    title: str
    subtitle: Optional[str] = None
    payload: Dict = Field(default_factory=dict)
    source: str
    created_at: datetime


class TripPlanRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    status: TripPlanStatus
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    destinations: List[str] = Field(default_factory=list)
    start_location: Optional[str] = None
    travelers: Dict = Field(default_factory=dict)
    budget: Dict = Field(default_factory=dict)
    trip_types: List[str] = Field(default_factory=list)
    transportation: List[str] = Field(default_factory=list)
    accommodation: Optional[str] = None
    preferences: Dict = Field(default_factory=dict)
    special_requirements: Dict = Field(default_factory=dict)
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    answers: Dict = Field(default_factory=dict)
    itinerary_days: List[TripItineraryDayOut] = Field(default_factory=list)
    message_count: int = 0
    last_message: Optional[TripMessageOut] = None


class PlanGenerateResponse(BaseModel):
    trip: TripPlanRead
    status: str = "generated"


class TripChatRequest(BaseModel):
    message: str


class PlanChangeDay(BaseModel):
    day_number: Optional[int] = None
    location: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[TripDaySource] = None
    items: List[TripItineraryItemOut] | List[Dict] = Field(default_factory=list)


class TripPlanChange(BaseModel):
    intent: str = "unknown"
    summary: str = ""
    trip: Dict = Field(default_factory=dict)
    days: List[Dict] = Field(default_factory=list)
    days_remove: List[int] = Field(default_factory=list)


class ApplyEditRequest(BaseModel):
    change: TripPlanChange
    message_id: Optional[UUID] = None


class ApplyEditResponse(BaseModel):
    applied: List[Dict] = Field(default_factory=list)  # human-readable change entries
    days: List[TripItineraryDayOut] = Field(default_factory=list)
    trip: TripPlanRead


class PlanAcceptResponse(BaseModel):
    trip: TripPlanRead
    status: str = "accepted"


class TripChatResponse(BaseModel):
    reply: str
    message_id: UUID
    intent: Optional[str] = None
    proposed_plan_change: Optional[TripPlanChange] = None
    conversation_id: UUID


class AddRecommendationRequest(BaseModel):
    kind: str
    destination_id: Optional[UUID] = None
    title: str
    subtitle: Optional[str] = None
    payload: Dict = Field(default_factory=dict)


class AddRecommendationResponse(BaseModel):
    id: UUID
    trip_id: UUID
    kind: str
    title: str