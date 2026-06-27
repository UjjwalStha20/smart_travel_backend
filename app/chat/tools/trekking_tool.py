from typing import Optional

from sqlmodel import Session

from app.services.trekking_route_service import TrekkingRouteService

from . import json_safe


class TrekkingTool:
    def __init__(self, session: Session):
        self.service = TrekkingRouteService(session)

    def search_trekking_routes(
        self,
        difficulty: Optional[str] = None,
        max_days: Optional[int] = None,
        min_days: Optional[int] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        result = self.service.get_all_trekking_routes(offset=offset, limit=limit)
        items = json_safe(result.get("items", []))
        if difficulty:
            items = [r for r in items if r.get("difficulty") and r["difficulty"].lower() == difficulty.lower()]
        if min_days is not None:
            items = [r for r in items if r.get("recommended_days") is not None and r["recommended_days"] >= min_days]
        if max_days is not None:
            items = [r for r in items if r.get("recommended_days") is not None and r["recommended_days"] <= max_days]
        return json_safe({
            "found": len(items),
            "total": result.get("total", len(items)),
            "trekking_routes": [
                {
                    "id": r.get("id"),
                    "route_name": r.get("route_name"),
                    "difficulty": r.get("difficulty"),
                    "total_distance_km": r.get("total_distance_km"),
                    "recommended_days": r.get("recommended_days"),
                    "max_altitude": r.get("max_altitude"),
                    "description": r.get("description", "")[:200],
                }
                for r in items
            ],
        })

    def get_trekking_route_by_id(self, route_id: str) -> dict:
        try:
            route = self.service.get_trekking_route_by_id(route_id)
            data = json_safe(route.model_dump() if hasattr(route, "model_dump") else route)
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_trekking_routes",
                    "description": "Search for trekking routes with optional filters by difficulty, duration, or distance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "moderate", "hard"],
                                "description": "Filter by difficulty level",
                            },
                            "max_days": {
                                "type": "integer",
                                "description": "Maximum recommended days",
                            },
                            "min_days": {
                                "type": "integer",
                                "description": "Minimum recommended days",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trekking_route_by_id",
                    "description": "Get detailed information about a specific trekking route by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "route_id": {
                                "type": "string",
                                "description": "The UUID of the trekking route",
                            },
                        },
                        "required": ["route_id"],
                    },
                },
            },
        ]
