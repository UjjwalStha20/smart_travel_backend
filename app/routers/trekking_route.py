from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import TrekkingRoute, User
from app.schemas import TrekkingRouteCreate, TrekkingRouteUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import TrekkingRouteService

router = APIRouter(prefix="/trekking-routes", tags=["Trekking Routes"])

class TrekkingRouteRouter:

    @router.get("/", response_model=PaginatedResponse[TrekkingRoute], status_code=200)
    async def get_trekking_routes(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        return TrekkingRouteService(session).get_all_trekking_routes(offset=offset, limit=limit)

    @router.get("/{route_id}", response_model=TrekkingRoute, status_code=200)
    async def get_trekking_route_by_id(route_id: str, session: SessionDep):
        return TrekkingRouteService(session).get_trekking_route_by_id(route_id)

    @router.post("/", response_model=TrekkingRoute, status_code=201)
    async def create_trekking_route(route_data: TrekkingRouteCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return TrekkingRouteService(session).create_trekking_route(route_data)

    @router.put("/{route_id}", response_model=TrekkingRoute, status_code=200)
    async def update_trekking_route(route_id: str, route_data: TrekkingRouteUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return TrekkingRouteService(session).update_trekking_route(route_id, route_data)

    @router.delete("/{route_id}", status_code=200)
    async def delete_trekking_route(route_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        return TrekkingRouteService(session).delete_trekking_route(route_id)
