from typing import Optional

from sqlmodel import Session

from app.services.destination_service import DestinationService

from . import json_safe


class DestinationTool:
    def __init__(self, session: Session):
        self.service = DestinationService(session)

    def _flatten_address(self, address: Optional[dict]) -> Optional[str]:
        """Helper to flatten nested address dict into a readable string for the AI."""
        if not address:
            return None
        # Adjust these keys based on your actual Address SQLModel
        parts = [
            address.get("place"), 
            address.get("district"), 
            address.get("province")
        ]
        return ", ".join([p for p in parts if p])

    def _summarize_trekking_routes(self, routes: Optional[list]) -> Optional[list]:
        """Helper to summarize trekking routes so we don't flood the AI with route point coordinates."""
        if not routes:
            return None
        
        summarized = []
        for route in routes:
            # Only give the AI the high-level overview of the trek
            summarized.append({
                "route_name": route.get("route_name"),
                "difficulty": route.get("difficulty"),
                "recommended_days": route.get("recommended_days"),
                "max_altitude": route.get("max_altitude"),
                # If you have a summary description, include it. Otherwise, just the basics.
                "description": (route.get("description") or "")[:150] 
            })
        return summarized

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
        # Delegate to service (SQL level filtering - perfect!)
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
        
        # Format the payload specifically for the AI
        ai_ready_destinations = []
        for d in result["items"]:
            ai_ready_destinations.append({
                "id": str(d["id"]),
                "name": d["name"],
                "category": d["category"],
                "description": (d["description"][:200] + "...") if d["description"] and len(d["description"]) > 200 else d.get("description", ""),
                "rating": d.get("rating"),
                "permit_required": d.get("permit_required"),
                "best_time": d.get("best_time"),
                # FIX: Flatten address to a simple string like "Pokhara, Kaski, Gandaki"
                "location": self._flatten_address(d.get("address")), 
            })

        return json_safe({
            "found": len(ai_ready_destinations),
            "total": result["total"],
            "destinations": ai_ready_destinations,
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
                # FIX: Flatten address
                "location": self._flatten_address(dest.get("address")),
                # FIX: Summarize trekking routes to prevent context window overflow
                "trekking_routes_overview": self._summarize_trekking_routes(dest.get("trekking_routes")),
                # If attraction exists, just pass its basic info, not the whole nested object
                "attraction_info": {
                    "types": dest.get("attraction", {}).get("attraction_types") if dest.get("attraction") else None,
                    "visit_duration_hours": dest.get("attraction", {}).get("visit_duration_hours") if dest.get("attraction") else None
                } if dest.get("attraction") else None
            })
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_destinations",
                    "description": "Search for travel destinations in Nepal. Use this to find destinations by name, category (attraction/trek), location (province/district/place), minimum rating, or permit requirements.",
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
                                "description": "Filter by province name (e.g., 'Gandaki')",
                            },
                            "district": {
                                "type": "string",
                                "description": "Filter by district name (e.g., 'Kaski')",
                            },
                            "place": {
                                "type": "string",
                                "description": "Filter by specific place name (e.g., 'Pokhara')",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_destination_by_id",
                    "description": "Get comprehensive details about a specific destination by its ID. Use this AFTER search_destinations when the user wants more details about a specific place.",
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