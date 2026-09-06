from sqlmodel import Session

from app.services.flight_info import get_flight_options

from . import json_safe


class FlightTool:
    def __init__(self, session: Session):
        self.session = session

    def get_flight_options(self, destination_id: str) -> dict:
        """
        Returns indicative flight/how-to-reach info for a destination: nearest airports,
        airlines, approximate duration and fare, and booking-portal links (informational only).
        """
        try:
            return json_safe(get_flight_options(self.session, destination_id))
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_flight_options",
                    "description": (
                        "Get flight and how-to-reach information for a destination: closest "
                        "airports, domestic airlines, indicative flight duration and fare ranges, "
                        "and booking portal links. Informational only - the app does NOT book "
                        "flights. Use this when the user asks how to get to a place or about flights."
                    ),
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
            }
        ]