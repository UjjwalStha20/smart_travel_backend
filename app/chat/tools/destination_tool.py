from typing import Optional

from sqlmodel import Session

from app.services.destination_service import DestinationService

from . import json_safe


class DestinationTool:
    def __init__(self, session: Session):
        self.service = DestinationService(session)

    def search_destinations(
        self,
        category: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rating_min: Optional[int] = None,
        permit_required: Optional[bool] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        place: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        result = self.service.get_destinations(
            offset=offset,
            limit=limit,
            category=category,
            name=name,
            description=description,
            rating_min=rating_min,
            permit_required=permit_required,
            province=province,
            district=district,
            place=place,
        )
        return json_safe({
            "found": len(result["items"]),
            "total": result["total"],
            "destinations": [
                {
                    "id": str(d["id"]),
                    "name": d["name"],
                    "category": d["category"],
                    "description": d["description"][:200] if d["description"] else "",
                    "rating": d.get("rating"),
                    "permit_required": d.get("permit_required"),
                    "best_time": d.get("best_time"),
                    "address": d.get("address"),
                    "attraction": d.get("attraction"),
                }
                for d in result["items"]
            ],
        })

    def get_destination_by_id(self, destination_id: str) -> dict:
        try:
            result = self.service.get_destination_by_id(destination_id)
            dest = result["destination"]
            return json_safe({
                "id": str(dest["id"]),
                "name": dest["name"],
                "category": dest["category"],
                "description": dest["description"],
                "rating": dest.get("rating"),
                "permit_required": dest.get("permit_required"),
                "best_time": dest.get("best_time"),
                "address": dest.get("address"),
                "attraction": dest.get("attraction"),
                "trekking_routes": dest.get("trekking_routes"),
            })
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_destinations",
                    "description": "Search for travel destinations in Nepal with optional filters. Use this to find destinations by name, category (attraction/trek), location (province/district/place), minimum rating, or permit requirements.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["attraction", "trek"],
                                "description": "Filter by destination category",
                            },
                            "name": {
                                "type": "string",
                                "description": "Search by destination name (partial match)",
                            },
                            "description": {
                                "type": "string",
                                "description": "Search within description text",
                            },
                            "rating_min": {
                                "type": "integer",
                                "description": "Minimum rating filter (1-5)",
                            },
                            "permit_required": {
                                "type": "boolean",
                                "description": "Filter by whether a permit is required",
                            },
                            "province": {
                                "type": "string",
                                "description": "Filter by province name",
                            },
                            "district": {
                                "type": "string",
                                "description": "Filter by district name",
                            },
                            "place": {
                                "type": "string",
                                "description": "Filter by specific place name",
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Pagination offset",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return (max 50)",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_destination_by_id",
                    "description": "Get comprehensive details about a specific destination by its ID, including full description, attraction info, entry fees, or trekking routes with route points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_id": {
                                "type": "string",
                                "description": "The UUID of the destination",
                            },
                        },
                        "required": ["destination_id"],
                    },
                },
            },
        ]
