from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Review


class ReviewService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_reviews(self, offset: int = 0, limit: int = 100):
        statement = select(Review).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_review_by_id(self, review_id: UUID) -> Review:
        review = self.session.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    def create_review(self, review_data: Review) -> Review:
        review = Review(**review_data.model_dump())
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def update_review(self, review_id: UUID, review_data: Review) -> Review:
        existing = self.get_review_by_id(review_id)
        patch = review_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_review(self, review_id: UUID) -> dict:
        review = self.get_review_by_id(review_id)
        self.session.delete(review)
        self.session.commit()
        return {"message": "Review deleted successfully"}
