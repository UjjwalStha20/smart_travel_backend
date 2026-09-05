from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.db import get_session, init_db
from app.dependencies import CurrentUser, SessionDep
from app.models import User
from app.schemas.recommendations.basics import (
    RecommendationCreate,
    RecommendationRead,
    RecommendationSummary,
)
from app.services.recommendation_service import (
    get_recommendation_service,
    RecommendationService,
)
from typing import Optional


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/",
    response_model=list[RecommendationRead],
    summary="Get personalized destination recommendations",
    description="Get personalized travel destination recommendations based on user profile, preferences, and behavior.",
)
async def get_recommendations(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(
        default=10, ge=1, le=50, description="Maximum number of recommendations to return"
    ),
) -> list[RecommendationRead]:
    """
    Get personalized destination recommendations for the authenticated user.

    The recommendation engine uses a hybrid approach combining:
    - Content-based filtering (destination features, description, category)
    - Structured preference matching (budget, duration, difficulty, interests, season)
    - Context-aware filtering (season, permits, altitude, duration fitting)
    - Collaborative filtering (behavior of similar users)
    - Popularity component (overall popular destinations)

    Returns ranked destinations with explanation of why each was recommended.
    """
    # Get the recommendation service
    rec_service: RecommendationService = get_recommendation_service(session)

    # Get recommendations
    recommendations = rec_service.get_recommendations(
        user_id=UUID(current_user.id) if hasattr(current_user, "id") else current_user.id,
        limit=limit,
    )

    return recommendations


@router.get(
    "/summary",
    response_model=list[RecommendationSummary],
    summary="Get recommendation summaries",
    description="Get shortened recommendation data suitable for list displays.",
)
async def get_recommendation_summaries(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[RecommendationSummary]:
    """
    Get shortened recommendation summaries for list displays.

    Returns minimal information: destination ID, name, category, score, and reason.
    """
    rec_service: RecommendationService = get_recommendation_service(session)
    recommendations = rec_service.get_recommendations(
        user_id=UUID(current_user.id) if hasattr(current_user, "id") else current_user.id,
        limit=limit,
    )

    # Convert to summary model
    summaries = []
    for rec in recommendations:
        summaries.append(
            RecommendationSummary(
                destination_id=rec.destination_id,
                name=rec.name,
                category=rec.category,
                final_score=rec.final_score,
                rank=rec.rank if hasattr(rec, "rank") else 1,
                reason_summary=rec.explanation.reason_summary if rec.explanation else None,
            )
        )

    return summaries


@router.post(
    "/interaction",
    summary="Record user-interaction for a destination",
    description="Record user interaction (view, click, save, rating, itinerary, booking) with a destination "
                "to improve future recommendations via collaborative filtering.",
)
async def record_interaction(
    session: SessionDep,
    current_user: CurrentUser,
    destination_id: UUID = Query(..., description="Destination ID interacted with"),
    interaction_type: str = Query(
        ..., description="Type of interaction: view, click, save, rating, itinerary, booking"
    ),
    rating: Optional[int] = Query(
        default=None, ge=1, le=5, description="Rating 1-5 if interaction type is 'rating'"
    ),
) -> JSONResponse:
    """
    Record a user-interaction with a destination.

    Supported interaction types:
    - view: User viewed the destination page
    - click: User clicked on the destination
    - save: User saved the destination to their saved list
    - rating: User rated the destination (1-5 stars)
    - itinerary: User added to itinerary
    - booking: User made a booking

    Ratings improve both collaborative filtering and structured preference matching.
    """
    try:
        rec_service: RecommendationService = get_recommendation_service(session)

        interaction = rec_service.record_interaction(
            user_id=UUID(current_user.id) if hasattr(current_user, "id") else current_user.id,
            destination_id=destination_id,
            interaction_type=interaction_type,
            rating=rating,
        )

        return JSONResponse(
            content={"message": "Interaction recorded successfully", "interaction_id": str(interaction.id)},
            status_code=201,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")


@router.post(
    "/preferences",
    summary="Update user preferences",
    description="Update user's declared preferences for better recommendation personalization.",
)
async def update_preferences(
    session: SessionDep,
    current_user: CurrentUser,
    preferred_categories: Optional[List[str]] = Query(
        default=None, description="Preferred destination categories"
    ),
    preferred_activities: Optional[List[str]] = Query(
        default=None, description="Preferred activities (e.g., hiking, cultural, wildlife)"
    ),
    budget_preference: Optional[str] = Query(
        default=None, description="Preferred budget level: budget, standard, luxury"
    ),
    typical_duration: Optional[int] = Query(
        default=None, ge=1, description="Typical trip duration in days"
    ),
    difficulty_preference: Optional[str] = Query(
        default=None, description="Preferred difficulty: easy, moderate, hard"
    ),
    preferred_season: Optional[List[str]] = Query(
        default=None, description="Preferred seasons (e.g., ['spring', 'autumn'])"
    ),
    travel_style: Optional[str] = Query(
        default=None, description="Preferred travel style: cultural, adventure, budget, luxury"
    ),
) -> JSONResponse:
    """
    Update user preferences in the database.

    These preferences are used by the structured preference matching component
    to provide more personalized recommendations.
    """
    from app.models import UserPreferences
    from datetime import datetime, timezone

    user_id = UUID(current_user.id) if hasattr(current_user, "id") else current_user.id

    # Check if preferences exist
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    existing = session.exec(stmt).first()

    if existing:
        # Update existing preferences
        if preferred_categories is not None:
            existing.preferred_categories = preferred_categories
        if preferred_activities is not None:
            existing.preferred_activities = preferred_activities
        if budget_preference is not None:
            existing.budget_preference = budget_preference
        if typical_duration is not None:
            existing.typical_duration = typical_duration
        if difficulty_preference is not None:
            existing.difficulty_preference = difficulty_preference
        if preferred_season is not None:
            existing.preferred_season = preferred_season
        if travel_style is not None:
            existing.travel_style = travel_style
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
    else:
        # Create new preferences
        new_prefs = UserPreferences(
            user_id=user_id,
            preferred_categories=preferred_categories or [],
            preferred_activities=preferred_activities or [],
            budget_preference=budget_preference,
            typical_duration=typical_duration,
            difficulty_preference=difficulty_preference,
            preferred_season=preferred_season or [],
            travel_style=travel_style or "cultural",
            updated_at=datetime.now(timezone.utc),
        )
        session.add(new_prefs)
        session.commit()
        session.refresh(new_prefs)

    return JSONResponse(
        content={"message": "Preferences updated successfully"},
        status_code=201,
    )
