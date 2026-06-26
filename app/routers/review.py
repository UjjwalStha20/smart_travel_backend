from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import Review
from app.schemas import ReviewCreate, ReviewUpdate
from app.services import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])

class ReviewRouter:

    @router.get("/", response_model=list[Review], status_code=200)
    async def get_reviews(session: SessionDep):
        return ReviewService(session).get_all_reviews(offset=0, limit=100)

    @router.get("/{review_id}", response_model=Review, status_code=200)
    async def get_review_by_id(review_id: str, session: SessionDep):
        return ReviewService(session).get_review_by_id(review_id)

    @router.post("/", response_model=Review, status_code=201)
    async def create_review(review_data: ReviewCreate, session: SessionDep):
        return ReviewService(session).create_review(review_data)

    @router.put("/{review_id}", response_model=Review, status_code=200)
    async def update_review(review_id: str, review_data: ReviewUpdate, session: SessionDep):
        return ReviewService(session).update_review(review_id, review_data)

    @router.delete("/{review_id}", status_code=200)
    async def delete_review(review_id: str, session: SessionDep):
        return ReviewService(session).delete_review(review_id)
