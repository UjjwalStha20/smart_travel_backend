from typing import List, Optional

from sqlmodel import Session

from app.services.route_optimizer import RouteOptimizer

from . import json_safe


class RouteOptimizerTool:
    def __init__(self, session: Session):
        self.service = RouteOptimizer(session)

    def optimize_trek_route(
        self,
        destination_id: Optional[str] = None,
        route_id: Optional[str] = None,
        points: Optional[List[dict]] = None,
    ) -> dict:
        """
        Optimizes a trekking route's waypoint order to minimize total distance
        (nearest-neighbour + 2-opt). Provide destination_id/route_id to use the
        DB route, or pass custom points.
        """
        try:
            result = self.service.optimize(
                route_id=str(route_id) if route_id else None,
                destination_id=str(destination_id) if destination_id else None,
                points=points or None,
            )
            return json_safe(result)
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "optimize_trek_route",
                    "description": (
                        "Optimize a trekking route by re-ordering its stops to minimize total "
                        "walking distance. Use this when the user wants the most efficient route "
                        "order, asks how to sequence a trek, or wonders if a route can be "
                        "shortened. Returns original vs optimized order and distance savings."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_id": {
                                "type": "string",
                                "description": "UUID of the destination whose trek route should be optimized",
                            },
                            "route_id": {
                                "type": "string",
                                "description": "UUID of a specific trekking route (preferred if known)",
                            },
                            "points": {
                                "type": "array",
                                "description": "Optional custom waypoints: [{\"name\", \"latitude\", \"longitude\"}]",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
                                        "overnight": {"type": "boolean"},
                                    },
                                },
                            },
                        },
                    },
                },
            }
        ]