from typing import Optional

from sqlmodel import Session

from app.services.food_cost_service import FoodCostService

from . import json_safe


class FoodCostTool:
    def __init__(self, session: Session):
        self.service = FoodCostService(session)

    def search_food_costs(
        self,
        max_budget_price: Optional[float] = None,
        min_budget_price: Optional[float] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        result = self.service.get_all_food_costs(offset=offset, limit=limit)
        items = json_safe(result.get("items", []))
        if min_budget_price is not None:
            items = [f for f in items if f.get("budget_price") is not None and float(f["budget_price"]) >= min_budget_price]
        if max_budget_price is not None:
            items = [f for f in items if f.get("budget_price") is not None and float(f["budget_price"]) <= max_budget_price]
        return json_safe({
            "found": len(items),
            "total": result.get("total", len(items)),
            "food_costs": [
                {
                    "id": f.get("id"),
                    "budget_price": f.get("budget_price"),
                    "standard_price": f.get("standard_price"),
                    "luxury_price": f.get("luxury_price"),
                }
                for f in items
            ],
        })

    def get_food_cost_by_id(self, food_cost_id: str) -> dict:
        try:
            fc = self.service.get_food_cost_by_id(food_cost_id)
            data = json_safe(fc.model_dump() if hasattr(fc, "model_dump") else fc)
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_food_costs",
                    "description": "Search for food cost information with optional price filters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_budget_price": {
                                "type": "number",
                                "description": "Maximum budget price",
                            },
                            "min_budget_price": {
                                "type": "number",
                                "description": "Minimum budget price",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_food_cost_by_id",
                    "description": "Get detailed food cost information by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "food_cost_id": {
                                "type": "string",
                                "description": "The UUID of the food cost entry",
                            },
                        },
                        "required": ["food_cost_id"],
                    },
                },
            },
        ]
