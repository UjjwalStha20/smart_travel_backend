
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep, require_admin
from app.models import User
from app.models.food_cost_model import FoodCost
from app.schemas import FoodCostCreate , FoodCostUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.food_cost_service import FoodCostService


router = APIRouter(prefix="/food_costs", tags=["Food Costs"])

class FoodCostRouter:
    @router.get("/",response_model=PaginatedResponse[FoodCost], status_code=200)
    async def get_food_costs(session : SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
        """Get all food costs."""
        return FoodCostService(session).get_all_food_costs(offset=offset, limit=limit)

    @router.get("/{food_id}", response_model=FoodCost,status_code=200)
    async def get_food_cost_by_id(food_id: str, session: SessionDep):
        """Get a food cost by ID."""
        return FoodCostService(session).get_food_cost_by_id(food_id)

    @router.post("/", response_model=FoodCost, status_code=201)
    async def create_food_cost(food_data: FoodCostCreate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Create a new food cost."""
        return FoodCostService(session).create_food_cost(food_data)

    @router.put("/{food_id}", response_model=FoodCost, status_code=200)
    async def update_food_cost(food_id: str, food_data: FoodCostUpdate, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Update a food cost by ID."""
        return FoodCostService(session).update_food_cost(food_id, food_data)

    @router.delete("/{food_id}", status_code=200)
    async def delete_food_cost(food_id: str, session: SessionDep, admin: Annotated[User, Depends(require_admin)]):
        """Delete a food cost by ID."""
        return FoodCostService(session).delete_food_cost(food_id)