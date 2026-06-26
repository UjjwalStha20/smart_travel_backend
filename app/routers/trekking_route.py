from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models import TrekkingRoute
from app.schemas import TrekkingRouteCreate, TrekkingRouteUpdate
from app.services import TrekkingRouteService

router = APIRouter(prefix="/trekking-routes", tags=["Trekking Routes"])

class TrekkingRouteRouter:

    @router.get("/", response_model=list[TrekkingRoute], status_code=200)
    async def get_trekking_routes(session: SessionDep):
        return TrekkingRouteService(session).get_all_trekking_routes(offset=0, limit=100)

    @router.get("/{route_id}", response_model=TrekkingRoute, status_code=200)
    async def get_trekking_route_by_id(route_id: str, session: SessionDep):
        return TrekkingRouteService(session).get_trekking_route_by_id(route_id)

    @router.post("/", response_model=TrekkingRoute, status_code=201)
    async def create_trekking_route(route_data: TrekkingRouteCreate, session: SessionDep):
        return TrekkingRouteService(session).create_trekking_route(route_data)

    @router.put("/{route_id}", response_model=TrekkingRoute, status_code=200)
    async def update_trekking_route(route_id: str, route_data: TrekkingRouteUpdate, session: SessionDep):
        return TrekkingRouteService(session).update_trekking_route(route_id, route_data)

    @router.delete("/{route_id}", status_code=200)
    async def delete_trekking_route(route_id: str, session: SessionDep):
        return TrekkingRouteService(session).delete_trekking_route(route_id)
