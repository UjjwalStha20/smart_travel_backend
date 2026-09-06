from typing import Optional

from sqlmodel import Session

from app.services.budget_optimizer import BudgetOptimizer

from . import json_safe


class BudgetOptimizerTool:
    def __init__(self, session: Session):
        self.service = BudgetOptimizer(session)

    def optimize_trip_budget(
        self,
        destination_id: str,
        total_budget: float,
        party_size: int = 1,
        days: int = 1,
        fee_category: str = "Foreign",
    ) -> dict:
        """
        Optimizes a trip budget for a destination: allocates accommodation, food,
        and permit/entry-fee costs within the total budget while maximizing comfort.
        """
        try:
            result = self.service.optimize(
                destination_id=str(destination_id),
                total_budget=float(total_budget),
                party_size=int(party_size or 1),
                days=int(days or 1),
                fee_category=str(fee_category or "Foreign"),
            )
            return json_safe(result)
        except Exception as e:
            return {"error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "optimize_trip_budget",
                    "description": (
                        "Optimize a trip budget for a destination in NPR. Allocates accommodation, "
                        "food, and trekking permit/entry fees across the given number of days and "
                        "party size, within a total budget. Use this when the user asks how much a "
                        "trip will cost, whether a budget fits, or what comfort level (budget/standard/"
                        "luxury) they can afford."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_id": {
                                "type": "string",
                                "description": "The UUID of the destination",
                            },
                            "total_budget": {
                                "type": "number",
                                "description": "Total trip budget in NPR for the whole party",
                            },
                            "party_size": {
                                "type": "integer",
                                "description": "Number of travelers (default 1)",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Trip duration in days (default 1)",
                            },
                            "fee_category": {
                                "type": "string",
                                "enum": ["Nepali", "SAARC", "Foreign"],
                                "description": "Pricing tier for permits/entry fees (default Foreign)",
                            },
                        },
                        "required": ["destination_id", "total_budget"],
                    },
                },
            }
        ]