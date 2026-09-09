from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import UserTrip


class UserTripService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_user_trips(self, offset: int = 0, limit: int = 100, user_id: UUID | None = None):
        statement = select(UserTrip)
        total_statement = select(func.count(UserTrip.id))
        if user_id:
            statement = statement.where(UserTrip.user_id == user_id)
            total_statement = total_statement.where(UserTrip.user_id == user_id)
        statement = statement.offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(total_statement).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_user_trip_by_id(self, trip_id: UUID) -> UserTrip:
        trip = self.session.get(UserTrip, trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="User trip not found")
        return trip

    def create_user_trip(self, trip_data: dict) -> UserTrip:
        trip = UserTrip(**trip_data)
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def update_user_trip(self, trip_id: UUID, trip_data: UserTrip) -> UserTrip:
        existing = self.get_user_trip_by_id(trip_id)
        patch = trip_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_user_trip(self, trip_id: UUID) -> dict:
        trip = self.get_user_trip_by_id(trip_id)
        self.session.delete(trip)
        self.session.commit()
        return {"message": "User trip deleted successfully"}
