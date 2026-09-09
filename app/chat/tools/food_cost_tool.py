from typing import Optional
from decimal import Decimal

from sqlmodel import Session

from app.services.food_cost_service import FoodCostService

from . import json_safe


class FoodCostTool:
    def __init__(self, session: Session):
        self.service = FoodCostService(session)

    def _get_location_context(self, route_points: list) -> Optional[str]:
        """Helper to extract the destination/route name from the route_points relationship."""
        if not route_points:
            return None
        
        # Just grab the first route point's destination/trek name to save tokens
        # Adjust these keys based on your actual RoutePoint/TrekkingRoute SQLModel
        first_point = route_points[0]
        
        # If RoutePoint has a direct destination name or trek name
        trek_name = first_point.get("trek_name") or first_point.get("destination_name")
        if trek_name:
            return trek_name
            
        # Fallback to route point name if available
        return first_point.get("name")

    def search_food_costs(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        max_budget_price: Optional[float] = None,
        min_budget_price: Optional[float] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        # FIX: Fetch a larger batch if filters are applied to prevent pagination bugs
        fetch_limit = 50 if (name or category or max_budget_price or min_budget_price) else limit
        
        result = self.service.get_all_food_costs(offset=offset, limit=fetch_limit)
        items = json_safe([
            f.model_dump() if hasattr(f, "model_dump") else f
            for f in result.get("items", [])
        ])

        # Apply filters safely
        filtered_items = []
        for f in items:
            name_match = not name or (f.get("name") and name.lower() in str(f["name"]).lower())
            cat_match = not category or (f.get("category") and category.lower() in str(f["category"]).lower())
            max_price_match = max_budget_price is None or (float(f.get("budget_price", 0) or 0) <= max_budget_price)
            min_price_match = min_budget_price is None or (float(f.get("budget_price", 0) or 0) >= min_budget_price)

            if name_match and cat_match and max_price_match and min_price_match:
                filtered_items.append(f)

        return json_safe({
            "found": len(filtered_items),
            "total": result.get("total", len(filtered_items)),
            "food_costs": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),           # <-- ADDED
                    "category": f.get("category"),   # <-- ADDED
                    "budget_price": str(f.get("budget_price")),
                    "standard_price": str(f.get("standard_price")),
                    "luxury_price": str(f.get("luxury_price")),
                    # FIX: Tell the AI WHERE this food cost applies
                    "applies_to_location": self._get_location_context(f.get("route_points", [])) 
                }
                for f in filtered_items[:limit]
            ],
        })

    def get_food_cost_by_id(self, food_cost_id: str) -> dict:
        try:
            fc = self.service.get_food_cost_by_id(food_cost_id)
            data = json_safe(fc.model_dump() if hasattr(fc, "model_dump") else fc)
            
            return {
                "id": str(data.get("id")),
                "name": data.get("name"),
                "category": data.get("category"),
                "budget_price": str(data.get("budget_price")),
                "standard_price": str(data.get("standard_price")),
                "luxury_price": str(data.get("luxury_price")),
                "applies_to_location": self._get_location_context(data.get("route_points", []))
            }
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_food_costs",
                    "description": "Search for food and meal costs in Nepal. Use this to find out how much specific foods (like Dal Bhat, Momos) cost, or to check general meal prices by category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Search by food name (e.g., 'Dal Bhat', 'Momos', 'Tea')",
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category (e.g., 'Main Meal', 'Drink', 'Snack')",
                            },
                            "max_budget_price": {
                                "type": "number",
                                "description": "Maximum budget price in NPR",
                            },
                            "min_budget_price": {
                                "type": "number",
                                "description": "Minimum budget price in NPR",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_food_cost_by_id",
                    "description": "Get detailed pricing information for a specific food item by its ID.",
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