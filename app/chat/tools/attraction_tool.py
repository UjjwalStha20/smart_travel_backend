from typing import Optional

from sqlmodel import Session

from app.services.attraction_service import AttractionService

from . import json_safe


class AttractionTool:
    def __init__(self, session: Session):
        self.service = AttractionService(session)

    def search_attractions(
        self,
        attraction_types: Optional[str] = None,
        min_duration_hours: Optional[float] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        result = self.service.get_attractions(offset=offset, limit=limit)
        items = json_safe(result.get("items", []))
        if attraction_types:
            items = [
                a for a in items
                if a.get("attraction_types")
                and attraction_types.lower() in str(a["attraction_types"]).lower()
            ]
        if min_duration_hours is not None:
            items = [
                a for a in items
                if a.get("visit_duration_hours") is not None
                and float(a["visit_duration_hours"]) >= min_duration_hours
            ]
        return json_safe({
            "found": len(items),
            "total": result.get("total", len(items)),
            "attractions": [
                {
                    "id": a.get("id"),
                    "attraction_types": a.get("attraction_types"),
                    "opening_hours": a.get("opening_hours"),
                    "visit_duration_hours": a.get("visit_duration_hours"),
                    "destination_id": a.get("destination_id"),
                }
                for a in items
            ],
        })

    def get_attraction_by_id(self, attraction_id: str) -> dict:
        try:
            attr = self.service.get_attraction_by_id(attraction_id)
            data = json_safe(attr.model_dump() if hasattr(attr, "model_dump") else attr)
            return {"id": data.get("id"), "attraction_types": data.get("attraction_types"), "opening_hours": data.get("opening_hours"), "visit_duration_hours": data.get("visit_duration_hours")}
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_attractions",
                    "description": "Search for attractions with optional filters by type or minimum visit duration.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attraction_types": {
                                "type": "string",
                                "description": "Filter by attraction type (e.g., temple, heritage, hiking, lake, viewpoint)",
                            },
                            "min_duration_hours": {
                                "type": "number",
                                "description": "Minimum visit duration in hours",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_attraction_by_id",
                    "description": "Get detailed information about a specific attraction by ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attraction_id": {
                                "type": "string",
                                "description": "The UUID of the attraction",
                            },
                        },
                        "required": ["attraction_id"],
                    },
                },
            },
        ]
