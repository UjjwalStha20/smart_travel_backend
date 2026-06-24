
from fastapi import APIRouter

from app.dependencies import SessionDep
from app.models.food_cost_model import FoodCost
from app.services.food_cost_service import FoodCostService


router = APIRouter(prefix="/food_costs", tags=["Food Costs"])

class FoodCostRouter:
    @router.get("/",response_model=list[FoodCost], status_code=200)
    async def get_food_costs(session : SessionDep):
        """Get all food costs."""
        return FoodCostService(session).get_all_food_costs(offset=0, limit=100)

    @router.get("/{food_id}", response_model=FoodCost,status_code=200)
    async def get_food_cost_by_id(food_id: str, session: SessionDep):
        """Get a food cost by ID."""
        return FoodCostService(session).get_food_cost_by_id(food_id)

    @router.post("/", response_model=FoodCost, status_code=201)
    async def create_food_cost(food_data: FoodCost, session: SessionDep):
        """Create a new food cost."""
        return FoodCostService(session).create_food_cost(food_data)

    @router.put("/{food_id}", response_model=FoodCost, status_code=200)
    async def update_food_cost(food_id: str, food_data: FoodCost, session: SessionDep):
        """Update a food cost by ID."""
        return FoodCostService(session).update_food_cost(food_id, food_data)

    @router.delete("/{food_id}", status_code=200)
    async def delete_food_cost(food_id: str, session: SessionDep):
        """Delete a food cost by ID."""
        return FoodCostService(session).delete_food_cost(food_id)