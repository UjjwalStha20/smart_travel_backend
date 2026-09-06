from fastapi import APIRouter

from app.dependencies import CurrentUser, SessionDep
from app.schemas.optimization_schema import (
    BudgetOptimizeRequest,
    BudgetOptimizeResult,
    RouteOptimizeRequest,
    RouteOptimizeResult,
)
from app.services.budget_optimizer import BudgetOptimizer
from app.services.route_optimizer import RouteOptimizer


router = APIRouter(prefix="/optimization", tags=["Optimization"])


@router.post(
    "/budget",
    response_model=BudgetOptimizeResult,
    summary="Optimize trip budget",
    description="Allocate accommodation, food and permit/entry-fee costs for a trip "
    "within a total budget, maximizing comfort via a bounded greedy allocation.",
)
def optimize_budget(
    body: BudgetOptimizeRequest,
    session: SessionDep,
    _: CurrentUser,
) -> BudgetOptimizeResult:
    optimizer = BudgetOptimizer(session)
    return optimizer.optimize(
        destination_id=body.destination_id,
        total_budget=body.total_budget,
        party_size=body.party_size,
        days=body.days,
        fee_category=body.fee_category,
    )


@router.post(
    "/route",
    response_model=RouteOptimizeResult,
    summary="Optimize trekking route",
    description="Re-order a trekking route's waypoints to minimize total distance "
    "using nearest-neighbour construction + 2-opt local search (open-path TSP).",
)
def optimize_route(
    body: RouteOptimizeRequest,
    session: SessionDep,
    _: CurrentUser,
) -> RouteOptimizeResult:
    optimizer = RouteOptimizer(session)
    return optimizer.optimize(
        route_id=str(body.route_id) if body.route_id else None,
        destination_id=str(body.destination_id) if body.destination_id else None,
        points=body.points,
    )