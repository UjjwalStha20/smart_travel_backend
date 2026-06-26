from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.models import RoutePoint


class RoutePointService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_route_points(self, offset: int = 0, limit: int = 100):
        statement = select(RoutePoint).offset(offset).limit(limit)
        items = self.session.exec(statement).all()
        total = self.session.exec(select(func.count(RoutePoint.id))).one()
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def get_route_point_by_id(self, point_id: UUID) -> RoutePoint:
        point = self.session.get(RoutePoint, point_id)
        if not point:
            raise HTTPException(status_code=404, detail="Route point not found")
        return point

    def create_route_point(self, point_data: RoutePoint) -> RoutePoint:
        point = RoutePoint(**point_data.model_dump())
        self.session.add(point)
        self.session.commit()
        self.session.refresh(point)
        return point

    def update_route_point(self, point_id: UUID, point_data: RoutePoint) -> RoutePoint:
        existing = self.get_route_point_by_id(point_id)
        patch = point_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_route_point(self, point_id: UUID) -> dict:
        point = self.get_route_point_by_id(point_id)
        self.session.delete(point)
        self.session.commit()
        return {"message": "Route point deleted successfully"}
