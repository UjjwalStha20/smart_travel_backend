from typing import Optional

from sqlmodel import Session

from app.services.trekking_route_service import TrekkingRouteService
from app.services.permit_service import PermitService # Assuming you have this based on your Permit model
from app.services.destination_service import DestinationService # To get the region name

from . import json_safe


class TrekkingTool:
    def __init__(self, session: Session):
        self.route_service = TrekkingRouteService(session)
        self.permit_service = PermitService(session)
        self.destination_service = DestinationService(session)

    def _summarize_route_points(self, route_points: list) -> list:
        """
        Summarizes route points into a clean day-by-day itinerary.
        Strips out UUIDs and heavy nested objects to save tokens.
        """
        if not route_points:
            return []
        
        # Sort by sequence number just in case
        sorted_points = sorted(route_points, key=lambda x: x.get("sequence_no", 0))
        
        itinerary = []
        for point in sorted_points:
            itinerary.append({
                "day/stop": point.get("sequence_no"),
                "location": point.get("name"),
                "walking_hours": str(point.get("walking_hours_from_previous")),
                "is_overnight_stop": point.get("overnight_stop", False),
                # We don't need address_id or accommodation_id here, just the name!
            })
        return itinerary

    def _get_permit_info(self, destination_id: str) -> list:
        """Fetches required permits for the trek's destination."""
        try:
            permits = self.permit_service.get_by_destination_id(destination_id)
            items = (
                [p.model_dump() if hasattr(p, "model_dump") else p for p in permits]
                if isinstance(permits, list)
                else permits.get("items", [])
            )
            return [
                {
                    "category": p.get("category"), # e.g., "Foreign", "SAARC"
                    "price_npr": str(p.get("price"))
                } for p in json_safe(items)
            ]
        except Exception:
            return []

    def search_trekking_routes(
        self,
        difficulty: Optional[str] = None,
        max_days: Optional[int] = None,
        min_days: Optional[int] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        # FIX 1: Smart fetch limit to prevent pagination filtering bugs
        fetch_limit = 50 if (difficulty or max_days is not None or min_days is not None) else limit
        
        result = self.route_service.get_all_trekking_routes(offset=offset, limit=fetch_limit)
        items = json_safe([
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in result.get("items", [])
        ])

        # Apply filters safely in memory
        filtered_items = []
        for r in items:
            diff_match = not difficulty or (r.get("difficulty") and r["difficulty"].lower() == difficulty.lower())
            min_days_match = min_days is None or (r.get("recommended_days") is not None and r["recommended_days"] >= min_days)
            max_days_match = max_days is None or (r.get("recommended_days") is not None and r["recommended_days"] <= max_days)

            if diff_match and min_days_match and max_days_match:
                filtered_items.append(r)

        # FIX 2: Return rich context (location) instead of just the route name
        return json_safe({
            "found": len(filtered_items),
            "total": result.get("total", len(filtered_items)),
            "trekking_routes": [
                {
                    "id": str(r.get("id")),
                    "route_name": r.get("route_name"),
                    "difficulty": r.get("difficulty"),
                    "total_distance_km": str(r.get("total_distance_km")),
                    "recommended_days": r.get("recommended_days"),
                    "max_altitude": f"{r.get('max_altitude')}m" if r.get("max_altitude") else None,
                    "description": (r.get("description", "") or "")[:150],
                    "region": r.get("destination_name") or "Nepal", # Ensure your service joins the destination name!
                }
                for r in filtered_items[:limit]
            ],
        })

    def get_trekking_route_by_id(self, route_id: str) -> dict:
        try:
            route = self.route_service.get_trekking_route_by_id(route_id)
            data = json_safe(route.model_dump() if hasattr(route, "model_dump") else route)
            
            # FIX 3: Summarize the route points so the AI gets a clean itinerary
            itinerary_summary = self._summarize_route_points(data.get("route_points", []))
            
            # FIX 4: Fetch permit costs so the AI can warn the user about budget
            permit_info = self._get_permit_info(data.get("destination_id"))

            return {
                "id": str(data.get("id")),
                "route_name": data.get("route_name"),
                "difficulty": data.get("difficulty"),
                "total_distance_km": str(data.get("total_distance_km")),
                "recommended_days": data.get("recommended_days"),
                "max_altitude": f"{data.get('max_altitude')}m" if data.get("max_altitude") else None,
                "description": data.get("description"),
                "daily_itinerary": itinerary_summary,
                "required_permits": permit_info,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_trekking_routes",
                    "description": "Search for trekking routes in Nepal by difficulty, duration, or distance.",
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
                                "description": "Maximum recommended days for the trek",
                            },
                            "min_days": {
                                "type": "integer",
                                "description": "Minimum recommended days for the trek",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trekking_route_by_id",
                    "description": "Get comprehensive details about a specific trekking route, including the daily itinerary and required permit costs. Use this AFTER search_trekking_routes.",
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