from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel, DateTime


class UserInteraction(SQLModel, table=True):
    __tablename__ = "user_interactions"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        description="User who performed the interaction",
    )

    destination_id: UUID = Field(
        foreign_key="destination.id",
        description="Destination involved in the interaction",
    )

    interaction_type: str = Field(
        description="Type of interaction: view, click, save, rating, itinerary, booking",
    )

    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Rating 1-5 if interaction_type is 'rating', otherwise None",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # Composite index for querying user's interaction history
    class Indexes:
        user_dest_type = ("user_id", "destination_id", "interaction_type")
