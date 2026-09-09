from datetime import date as DateType
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import JSON, Column, DateTime

if TYPE_CHECKING:
    from app.models import User


class TripPlanStatus(str, Enum):
    draft = "draft"
    planning = "planning"
    accepted = "accepted"
    completed = "completed"


class TripDaySource(str, Enum):
    generated = "generated"
    edited = "edited"
    ai = "ai"
    accepted = "accepted"


# ---------------------------------------------------------------------------
# Trip Plan — the structured trip object (one per user-planning session)
# ---------------------------------------------------------------------------

class TripPlan(SQLModel, table=True):
    __tablename__ = "trip_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    name: str
    status: TripPlanStatus = TripPlanStatus.draft

    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    duration_days: Optional[int] = None

    destinations: List[str] = Field(default=list, sa_type=JSON)
    start_location: Optional[str] = None

    travelers: Dict = Field(default=dict, sa_type=JSON)
    budget: Dict = Field(default=dict, sa_type=JSON)
    trip_types: List[str] = Field(default=list, sa_type=JSON)
    transportation: List[str] = Field(default=list, sa_type=JSON)
    accommodation: Optional[str] = None

    preferences: Dict = Field(default=dict, sa_type=JSON)
    special_requirements: Dict = Field(default=dict, sa_type=JSON)

    summary: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    user: "User" = Relationship(back_populates="trip_plans")
    preference: Optional["TripPreference"] = Relationship(
        back_populates="trip", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    itinerary_days: List["TripItineraryDay"] = Relationship(
        back_populates="trip", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    conversation: Optional["TripConversation"] = Relationship(
        back_populates="trip", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    edits: List["TripEdit"] = Relationship(
        back_populates="trip", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    recommendations: List["TripRecommendation"] = Relationship(
        back_populates="trip", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TripPreference(SQLModel, table=True):
    __tablename__ = "trip_preferences"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trip_id: UUID = Field(foreign_key="trip_plans.id", unique=True)

    answers: Dict = Field(default=dict, sa_type=JSON)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trip: "TripPlan" = Relationship(back_populates="preference")


class TripItineraryDay(SQLModel, table=True):
    __tablename__ = "trip_itinerary_days"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trip_id: UUID = Field(foreign_key="trip_plans.id", index=True)
    day_number: int
    date: Optional[DateType] = None
    location: Optional[str] = None
    title: Optional[str] = None
    transportation: List[str] = Field(default=list, sa_type=JSON)
    estimated_duration_hours: Optional[float] = None
    notes: Optional[str] = None
    status: TripDaySource = TripDaySource.generated
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trip: "TripPlan" = Relationship(back_populates="itinerary_days")
    items: List["TripItineraryItem"] = Relationship(
        back_populates="day", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TripItineraryItem(SQLModel, table=True):
    __tablename__ = "trip_itinerary_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    day_id: UUID = Field(foreign_key="trip_itinerary_days.id", index=True)
    position: int = 0
    title: str
    category: Optional[str] = None
    location: Optional[str] = None
    duration_hours: Optional[float] = None
    notes: Optional[str] = None
    recommendation_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    day: "TripItineraryDay" = Relationship(back_populates="items")


class TripConversation(SQLModel, table=True):
    __tablename__ = "trip_conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trip_id: UUID = Field(foreign_key="trip_plans.id", unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trip: "TripPlan" = Relationship(back_populates="conversation")
    messages: List["TripMessage"] = Relationship(
        back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TripMessage(SQLModel, table=True):
    __tablename__ = "trip_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="trip_conversations.id", index=True)
    role: str
    content: str
    intent: Optional[str] = None
    meta: Dict = Field(default=dict, sa_type=JSON)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation: "TripConversation" = Relationship(back_populates="messages")


class TripEdit(SQLModel, table=True):
    __tablename__ = "trip_edits"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trip_id: UUID = Field(foreign_key="trip_plans.id", index=True)
    field: str
    new_value: str = ""
    origin: str = "ai"
    message_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trip: "TripPlan" = Relationship(back_populates="edits")


class TripRecommendation(SQLModel, table=True):
    __tablename__ = "trip_recommendations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trip_id: UUID = Field(foreign_key="trip_plans.id", index=True)
    kind: str
    destination_id: Optional[UUID] = None
    title: str
    subtitle: Optional[str] = None
    payload: Dict = Field(default=dict, sa_type=JSON)
    source: str = "chat"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trip: "TripPlan" = Relationship(back_populates="recommendations")