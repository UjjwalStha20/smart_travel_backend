from typing import Optional
from sqlmodel import Session
from app.services.attraction_service import AttractionService
from app.services.entry_fee_service import EntryFeeService # Assuming you have this
from . import json_safe

class AttractionTool:
    def __init__(self, session: Session):
        self.attraction_service = AttractionService(session)
        self.entry_fee_service = EntryFeeService(session)

    def get_attraction_details(self, destination_id: str) -> dict:
        """
        Fetches specific attraction details (hours, duration, fees) for a given destination.
        Use this AFTER search_destinations when the user asks about visiting hours or entry fees.
        """
        try:
            # Fetch the attraction linked to this destination
            attraction = self.attraction_service.get_by_destination_id(destination_id)
            if not attraction:
                return {"error": "This destination does not have specific attraction details (it might be a trek)."}
            
            data = json_safe(attraction.model_dump() if hasattr(attraction, "model_dump") else attraction)
            
            # Fetch related entry fees
            fees = []
            try:
                entry_fees = self.entry_fee_service.get_by_attraction_id(data["id"])
                fees = json_safe([f.model_dump() for f in entry_fees]) if entry_fees else []
            except Exception:
                pass # Fallback if service method doesn't exist yet

            return {
                "destination_id": str(data["destination_id"]),
                "attraction_types": data.get("attraction_types"),
                "opening_hours": data.get("opening_hours"),
                "visit_duration_hours": str(data.get("visit_duration_hours")),
                "entry_fees": [
                    {
                        "category": f.get("category"), # e.g., "Foreigner", "SAARC", "Local"
                        "price_npr": str(f.get("price_npr"))
                    } for f in fees
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    def search_attractions_by_type(self, attraction_type: str, limit: int = 5) -> dict:
        """
        Finds attractions of a specific type (e.g., 'temple', 'lake').
        Note: This relies on your DestinationService to filter by category='attraction' 
        and join the Attraction table.
        """
        try:
            # You will need to implement this in your DestinationService or AttractionService
            # It should query Destination where category='attraction' and attraction_types contains the type
            results = self.attraction_service.search_by_type(attraction_type, limit=limit)
            
            return json_safe({
                "found": len(results),
                "attractions": [
                    {
                        "name": r.get("name"), # From Destination table
                        "location": r.get("address"), # From Destination table
                        "types": r.get("attraction_types"),
                        "duration_hours": str(r.get("visit_duration_hours"))
                    } for r in results
                ]
            })
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_attraction_details",
                    "description": "Get specific details about an attraction, including opening hours, visit duration, and entry fees. Use this AFTER finding the destination ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_id": {
                                "type": "string",
                                "description": "The UUID of the destination (attraction)",
                            },
                        },
                        "required": ["destination_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_attractions_by_type",
                    "description": "Find attractions in Nepal by a specific type (e.g., 'temple', 'heritage', 'lake', 'hiking').",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "attraction_type": {
                                "type": "string",
                                "description": "The type of attraction to search for",
                            },
                        },
                        "required": ["attraction_type"],
                    },
                },
            },
        ]