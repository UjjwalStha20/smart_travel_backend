from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import TrekkingRoute


class TrekkingRouteService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_trekking_routes(self, offset: int = 0, limit: int = 100):
        statement = select(TrekkingRoute).offset(offset).limit(limit)
        return self.session.exec(statement).all()

    def get_trekking_route_by_id(self, route_id: UUID) -> TrekkingRoute:
        route = self.session.get(TrekkingRoute, route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Trekking route not found")
        return route

    def create_trekking_route(self, route_data: TrekkingRoute) -> TrekkingRoute:
        route = TrekkingRoute(**route_data.model_dump())
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def update_trekking_route(self, route_id: UUID, route_data: TrekkingRoute) -> TrekkingRoute:
        existing = self.get_trekking_route_by_id(route_id)
        patch = route_data.model_dump(exclude_unset=True)
        existing.sqlmodel_update(patch)
        self.session.commit()
        self.session.refresh(existing)
        return existing

    def delete_trekking_route(self, route_id: UUID) -> dict:
        route = self.get_trekking_route_by_id(route_id)
        self.session.delete(route)
        self.session.commit()
        return {"message": "Trekking route deleted successfully"}
