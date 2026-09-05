from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class SimilarityScore(BaseModel):
    """Base score information for a recommendation."""
    score: float = Field(ge=0.0, le=1.0, description="Normalized score between 0 and 1")
    max_possible: float = Field(default=1.0, description="Maximum possible score for this component")


class PreferenceMatch(BaseModel):
    """A matched user preference and its strength."""
    preference: str
    strength: float = Field(ge=0.0, le=1.0, description="Match strength 0.0 to 1.0")
    detail: Optional[str] = None


class ContextMatch(BaseModel):
    """A matched contextual factor and its strength."""
    factor: str
    satisfied: bool
    strength: float = Field(ge=0.0, le=1.0, description="How well factor matches 0.0 to 1.0")
    detail: Optional[str] = None


class ComponentScores(BaseModel):
    """Individual component scores for explainable recommendations."""
    content: float = Field(ge=0.0, le=1.0, default=0.0, description="Content-based similarity")
    preference: float = Field(ge=0.0, le=1.0, default=0.0, description="Structured preference matching")
    context: float = Field(ge=0.0, le=1.0, default=0.0, description="Context-aware scoring")
    collaborative: float = Field(ge=0.0, le=1.0, default=0.0, description="Collaborative filtering score")
    popularity: float = Field(ge=0.0, le=1.0, default=0.0, description="Popularity-based score")


class RecommendationExplanation(BaseModel):
    """Explanation for why a destination was recommended."""
    matched_preferences: List[PreferenceMatch] = Field(default_factory=list, description="User preferences matched")
    contextual_factors: List[ContextMatch] = Field(default_factory=list, description="Contextual factors considered")
    reason_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of why recommended"
    )


class RecommendationBase(BaseModel):
    """Base fields for a recommendation."""
    destination_id: UUID
    name: str
    category: str
    image_url: Optional[str] = Field(default=None, description="Featured image if available")
    final_score: float = Field(ge=0.0, le=1.0, description="Final hybrid recommendation score")
    component_scores: ComponentScores = Field(default_factory=ComponentScores)
    explanation: RecommendationExplanation = Field(default_factory=RecommendationExplanation)


class RecommendationCreate(BaseModel):
    """Input for creating a recommendation request."""
    user_id: UUID
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of recommendations")
    force_refresh: Optional[bool] = Field(
        default=False,
        description="Force recomputation even if cached recommendations exist",
    )


class RecommendationRead(RecommendationBase):
    """Read model for recommendations returned via API."""
    rank: int = Field(description="1-based rank in the recommendation list")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class RecommendationSummary(BaseModel):
    """Summary version for list views."""
    destination_id: UUID
    name: str
    category: str
    final_score: float
    rank: int
    reason_summary: Optional[str] = None
