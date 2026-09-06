from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetOptimizeRequest(BaseModel):
    destination_id: UUID = Field(description="Destination to budget for")
    total_budget: float = Field(ge=0, description="Total trip budget in NPR for the whole party")
    party_size: int = Field(default=1, ge=1, le=50, description="Number of travelers (accommodation is per room, food/fees per person)")
    days: int = Field(default=1, ge=1, le=60, description="Trip duration in days")
    fee_category: str = Field(
        default="Foreign",
        description="Pricing tier for permits/entry fees: Nepali, SAARC or Foreign",
    )


class BudgetDailyPlan(BaseModel):
    day: int
    food_tier: str
    food_cost: float
    accommodation_tier: str
    accommodation_cost: float
    day_total: float


class FeeBreakdown(BaseModel):
    name: str
    category: str
    price: float


class BudgetOptimizeResult(BaseModel):
    feasible: bool = Field(description="Whether the trip fits within the given budget")
    destination_id: UUID
    destination_name: str
    party_size: int
    days: int
    method: str = Field(description="Algorithm used to allocate the budget")
    minimum_budget: float = Field(description="Cheapest possible plan for this trip size/duration")
    accommodation_total: float
    food_total: float
    fees_total: float
    grand_total: float
    total_budget: float
    surplus: float
    deficit: Optional[float] = Field(default=None, description="How far over budget the cheapest plan is (feasible=False only)")
    per_person_total: float
    avg_daily_per_person: float
    comfort_score: float = Field(description="0-1 measure of comfort (tier level) achieved within budget")
    daily_plan: List[BudgetDailyPlan] = Field(default_factory=list)
    one_time_fees: List[FeeBreakdown] = Field(default_factory=list)


class RouteStopInput(BaseModel):
    name: str
    latitude: float
    longitude: float
    recorded_km: Optional[float] = Field(default=None, description="Distance from previous stop recorded in data (optional)")
    overnight: bool = False


class RouteOptimizeRequest(BaseModel):
    destination_id: Optional[UUID] = Field(default=None, description="Optimize the trek route of this destination")
    route_id: Optional[UUID] = Field(default=None, description="Optimize a specific trekking route")
    points: Optional[List[RouteStopInput]] = Field(
        default=None,
        description="Provide custom waypoints directly (overrides destination_id/route_id)",
    )


class RouteStop(BaseModel):
    sequence: int
    name: str
    distance_from_previous_km: float
    cumulative_km: float
    recorded_km: Optional[float] = None
    overnight: bool = False


class RouteOptimizeResult(BaseModel):
    route_name: str
    source: str
    method: str = Field(description="Algorithm used (nearest neighbour + 2-opt)")
    stops: int
    original_order: List[str]
    optimized_order: List[RouteStop]
    original_total_km: float
    optimized_total_km: float
    savings_km: float
    savings_percent: float
    total_walking_hours: Optional[float] = None