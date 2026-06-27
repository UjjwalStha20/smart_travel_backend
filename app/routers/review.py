from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentUser, SessionDep
from app.models import Review
from app.schemas import ReviewCreate, ReviewUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])

class ReviewRouter:

    @router.get("/", response_model=PaginatedResponse[Review], status_code=200)
    async def get_reviews(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return ReviewService(session).get_all_reviews(offset=offset, limit=limit)

    @router.get("/{review_id}", response_model=Review, status_code=200)
    async def get_review_by_id(review_id: str, session: SessionDep):
        return ReviewService(session).get_review_by_id(review_id)

    @router.post("/", response_model=Review, status_code=201)
    async def create_review(review_data: ReviewCreate, session: SessionDep, current_user: CurrentUser):
        data = review_data.model_dump() | {"user_id": current_user.id}
        return ReviewService(session).create_review(data)

    @router.put("/{review_id}", response_model=Review, status_code=200)
    async def update_review(review_id: str, review_data: ReviewUpdate, session: SessionDep, current_user: CurrentUser):
        existing = ReviewService(session).get_review_by_id(review_id)
        if existing.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your review")
        return ReviewService(session).update_review(review_id, review_data)

    @router.delete("/{review_id}", status_code=200)
    async def delete_review(review_id: str, session: SessionDep, current_user: CurrentUser):
        existing = ReviewService(session).get_review_by_id(review_id)
        if existing.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not your review")
        return ReviewService(session).delete_review(review_id)
