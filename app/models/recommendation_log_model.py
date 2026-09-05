from datetime import datetime, timezone
from typing import Optional, Dict
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel, DateTime, JSON


class RecommendationLog(SQLModel, table=True):
    __tablename__ = "recommendation_logs"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        description="User who received the recommendation",
    )

    destination_id: UUID = Field(
        foreign_key="destination.id",
        description="Destination that was recommended",
    )

    final_score: float = Field(
        description="Final hybrid recommendation score (0.0 to 1.0)",
    )

    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        sa_type=JSON,
        description="Individual component scores: content, preference, context, collaborative, popularity",
    )

    algorithm_version: str = Field(
        default="hybrid_v1",
        description="Version identifier for the algorithm used",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
