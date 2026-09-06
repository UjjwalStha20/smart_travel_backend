from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models import Address, Destination
from app.services.live_data import LiveDataError, fetch_weather

from . import json_safe


class WeatherTool:
    def __init__(self, session: Session):
        self.session = session

    def get_destination_weather(self, destination_id: str, days: Optional[int] = 5) -> dict:
        """
        Gets live current conditions + daily forecast for a destination's coordinates.
        """
        try:
            destination = self.session.get(Destination, UUID(str(destination_id)))
            if not destination:
                return {"error": "Destination not found"}
            address = (
                self.session.get(Address, destination.address_id)
                if destination.address_id
                else None
            )
            if not address or address.latitude is None or address.longitude is None:
                return {"error": "Destination has no GPS coordinates"}

            return json_safe(
                {
                    **fetch_weather(address.latitude, address.longitude, days=int(days or 5)),
                    "destination": destination.name,
                }
            )
        except LiveDataError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_destination_weather",
                    "description": (
                        "Get live weather for a destination: current temperature, condition, "
                        "humidity, wind, plus a daily forecast. Use this when the user asks about "
                        "today's weather, packing advice, rain risk, or the forecast for their trip."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_id": {
                                "type": "string",
                                "description": "The UUID of the destination",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of forecast days (1-14, default 5)",
                            },
                        },
                        "required": ["destination_id"],
                    },
                },
            }
        ]