from typing import Optional
from decimal import Decimal
from sqlmodel import Session
from app.services.accommodation_service import AccommodationService
from . import json_safe

class AccommodationTool:
    def __init__(self, session: Session):
        self.service = AccommodationService(session)

    def search_accommodations_by_price(
        self, 
        max_budget_price: Optional[float] = None,
        min_budget_price: Optional[float] = None,
        location: Optional[str] = None, # <-- ADDED: Allow AI to filter by location
        limit: int = 5
    ) -> dict:
        """
        Finds accommodations within a specific price range and/or location.
        """
        try:
            # Convert floats to Decimals for the service
            max_price = Decimal(str(max_budget_price)) if max_budget_price is not None else None
            min_price = Decimal(str(min_budget_price)) if min_budget_price is not None else None
            
            # Fetch slightly more results to account for client-side filtering
            results = self.service.search_by_price_range(
                min_price=min_price, 
                max_price=max_price, 
                limit=limit * 2
            )
            
            # Client-side location filter (in case your service doesn't support it natively)
            filtered_results = [
                r for r in results 
                if not location or (r.get("location") and location.lower() in str(r["location"]).lower())
            ]

            return json_safe({
                "found": len(filtered_results),
                "accommodations": [
                    {
                        "id": str(r.get("id")),
                        "name": r.get("name"),               # ✅ NEW: AI needs the name!
                        "description": (r.get("description") or "")[:150], # ✅ NEW: Brief context
                        "location": r.get("location"),         # ✅ NEW: Direct location field
                        "budget_price": str(r.get("budget_price")),
                        "standard_price": str(r.get("standard_price")),
                        "luxury_price": str(r.get("luxury_price")),
                    } for r in filtered_results[:limit]
                ]
            })
        except Exception as e:
            return {"error": str(e)}

    def get_accommodation_details(self, accommodation_id: str) -> dict:
        """
        Gets full details for a specific accommodation.
        """
        try:
            acc = self.service.get_by_id(accommodation_id)
            data = json_safe(acc.model_dump() if hasattr(acc, "model_dump") else acc)
            
            return {
                "id": str(data.get("id")),
                "name": data.get("name"),               # ✅ NEW
                "description": data.get("description"), # ✅ NEW
                "location": data.get("location"),       # ✅ NEW
                "budget_price": str(data.get("budget_price")),
                "standard_price": str(data.get("standard_price")),
                "luxury_price": str(data.get("luxury_price")),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_accommodations_by_price",
                    "description": "Search for accommodations (teahouses, lodges, resorts) based on budget price range and/or location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_budget_price": {
                                "type": "number",
                                "description": "Maximum budget price per night in NPR",
                            },
                            "min_budget_price": {
                                "type": "number",
                                "description": "Minimum budget price per night in NPR",
                            },
                            "location": {
                                "type": "string",
                                "description": "Optional location to filter by (e.g., 'Ghorepani', 'Pokhara')",
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_accommodation_details",
                    "description": "Get detailed information, description, and full pricing tiers for a specific accommodation.",
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