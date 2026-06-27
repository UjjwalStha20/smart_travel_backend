from typing import Optional

from sqlmodel import Session

from app.services.accommodation_service import AccommodationService

from . import json_safe


class AccommodationTool:
    def __init__(self, session: Session):
        self.service = AccommodationService(session)

    def search_accommodations(
        self,
        max_budget_price: Optional[float] = None,
        min_budget_price: Optional[float] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        result = self.service.get_all_accommodations(offset=offset, limit=limit)
        items = json_safe(result.get("items", []))
        if min_budget_price is not None:
            items = [a for a in items if a.get("budget_price") is not None and float(a["budget_price"]) >= min_budget_price]
        if max_budget_price is not None:
            items = [a for a in items if a.get("budget_price") is not None and float(a["budget_price"]) <= max_budget_price]
        return json_safe({
            "found": len(items),
            "total": result.get("total", len(items)),
            "accommodations": [
                {
                    "id": a.get("id"),
                    "budget_price": a.get("budget_price"),
                    "standard_price": a.get("standard_price"),
                    "luxury_price": a.get("luxury_price"),
                }
                for a in items
            ],
        })

    def get_accommodation_by_id(self, accommodation_id: str) -> dict:
        try:
            acc = self.service.get_accommodation_by_id(accommodation_id)
            data = json_safe(acc.model_dump() if hasattr(acc, "model_dump") else acc)
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_accommodations",
                    "description": "Search for accommodations with optional price filters.",
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
                    "name": "get_accommodation_by_id",
                    "description": "Get detailed information about a specific accommodation by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accommodation_id": {
                                "type": "string",
                                "description": "The UUID of the accommodation",
                            },
                        },
                        "required": ["accommodation_id"],
                    },
                },
            },
        ]
