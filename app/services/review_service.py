from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.models import Review


class ReviewService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_reviews(self, offset: int = 0, limit: int = 100):
        statement = select(Review).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(Review.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_review_by_id(self, review_id: UUID) -> Review:
        review = self.session.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review

    def create_review(self, review_data: dict) -> Review:
        existing = self.session.exec(
            select(Review).where(
                Review.user_id == review_data["user_id"],
                Review.destination_id == review_data["destination_id"],
            )
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="You already reviewed this destination")
        review = Review(**review_data)
        try:
            self.session.add(review)
            self.session.commit()
            self.session.refresh(review)
        except IntegrityError:
            self.session.rollback()
            raise HTTPException(status_code=409, detail="You already reviewed this destination")
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
