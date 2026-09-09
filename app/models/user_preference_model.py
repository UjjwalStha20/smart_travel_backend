from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel, DateTime, JSON


class UserPreferences(SQLModel, table=True):
    __tablename__ = "user_preferences"

    user_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        foreign_key="users.id",
    )

    preferred_categories: List[str] = Field(
        default=None,
        sa_type=JSON,
        description="Preferred destination categories (e.g., ['attraction', 'trek'])"
    )

    preferred_activities: List[str] = Field(
        default=None,
        sa_type=JSON,
        description="Preferred activities (e.g., ['hiking', 'cultural', 'wildlife'])"
    )

    budget_preference: Optional[str] = Field(
        default=None,
        description="Preferred budget level (budget, standard, luxury)"
    )

    typical_duration: Optional[int] = Field(
        default=None,
        description="Typical trip duration in days"
    )

    difficulty_preference: Optional[str] = Field(
        default=None,
        description="Preferred trekking difficulty (easy, moderate, hard)"
    )

    preferred_season: Optional[List[str]] = Field(
        default=None,
        sa_type=JSON,
        description="Preferred seasons (e.g., ['spring', 'autumn'])"
    )

    travel_style: Optional[str] = Field(
        default=None,
        description="Preferred travel style (cultural, adventure, budget, luxury)"
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
