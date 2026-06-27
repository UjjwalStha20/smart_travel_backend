from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import RoutePoint, User
from app.schemas import RoutePointCreate, RoutePointUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import RoutePointService

router = APIRouter(prefix="/route-points", tags=["Route Points"])

class RoutePointRouter:

    @router.get("/", response_model=PaginatedResponse[RoutePoint], status_code=200)
    async def get_route_points(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return RoutePointService(session).get_all_route_points(offset=offset, limit=limit)

    @router.get("/{point_id}", response_model=RoutePoint, status_code=200)
    async def get_route_point_by_id(point_id: str, session: SessionDep):
        return RoutePointService(session).get_route_point_by_id(point_id)

    @router.post("/", response_model=RoutePoint, status_code=201)
    async def create_route_point(point_data: RoutePointCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return RoutePointService(session).create_route_point(point_data)

    @router.put("/{point_id}", response_model=RoutePoint, status_code=200)
    async def update_route_point(point_id: str, point_data: RoutePointUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return RoutePointService(session).update_route_point(point_id, point_data)

    @router.delete("/{point_id}", status_code=200)
    async def delete_route_point(point_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return RoutePointService(session).delete_route_point(point_id)
