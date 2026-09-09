"""Budget optimization for a trip using a bounded greedy allocation.

Algorithm
---------
1. Build a per-tier cost model from the seeded price data:
   - accommodation cost per room/night (budget / standard / luxury)
   - food cost per person/day (summed across food categories per tier)
   - one-time per-person fees (trekking permits + attraction entry fees)
2. Feasibility check: the all-budget plan must fit within ``total_budget``.
3. Greedy upgrade (bounded knapsack-style): while surplus remains, apply the
   single upgrade (any component, any day) that costs the least, since each
   upgrade step buys exactly one more comfort point -> maximizes total comfort
   per NPR. Stops when no upgrade fits the remaining surplus.
"""
import statistics
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    Accommodation,
    Attraction,
    Destination,
    EntryFee,
    FoodCost,
    Permit,
)

TIER_KEYS = ["budget", "standard", "luxury"]
TIER_RANK = {"budget": 1, "standard": 2, "luxury": 3}


def _mean_tier_price(items, tier: str) -> Optional[Decimal]:
    """Mean of ``<tier>_price`` across items, ignoring missing/zero values."""
    values = [
        float(getattr(i, f"{tier}_price"))
        for i in items
        if getattr(i, f"{tier}_price") is not None and getattr(i, f"{tier}_price") > 0
    ]
    if not values:
        return None
    return Decimal(str(statistics.mean(values))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _category_value(row) -> str:
    val = getattr(row, "category", None)
    if hasattr(val, "value"):
        return str(val.value)
    return str(val)


def _pick_by_category(rows, requested: str):
    """Pick a priced row matching the requested category, with fallbacks."""
    requested = (requested or "Foreign").strip()
    for candidate in (requested, "Foreign", "SAARC", "Nepali"):
        for row in rows:
            if _category_value(row).lower() == candidate.lower():
                return row
    return rows[0] if rows else None


class BudgetOptimizer:
    def __init__(self, session: Session):
        self.session = session

    def _cost_model(self, destination_id, fee_category: str = "Foreign") -> dict:
        """Build the per-tier cost model for a destination.

        Returns callables/values shared by ``optimize`` and ``estimate``:
        - ``accom_price(tier_idx)``: price per room/night at a tier (0=budget..2=luxury)
        - ``food_daily(tier_idx)``:  total daily food cost per person at a tier
        - ``one_time_per_person``:   permits + entry fees for the requested category
        - ``destination``:           the destination model
        """
        destination = self.session.get(Destination, UUID(str(destination_id)))
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")

        # ---- Cost model -------------------------------------------------------
        accommodations = self.session.exec(select(Accommodation)).all()
        food_items = self.session.exec(select(FoodCost)).all()
        food_by_category = defaultdict(list)
        for fc in food_items:
            food_by_category[fc.category or "Other"].append(fc)

        def accom_price(tier_idx: int) -> Decimal:
            if tier_idx < 0:
                return Decimal("0.00")
            p = _mean_tier_price(accommodations, TIER_KEYS[tier_idx])
            return p if p is not None else accom_price(tier_idx - 1)

        def food_daily(tier_idx: int) -> Decimal:
            """Total daily food cost per person at the given tier."""
            totals = {t: Decimal("0.00") for t in range(3)}
            for tier_items in food_by_category.values():
                for t in range(3):
                    p = _mean_tier_price(tier_items, TIER_KEYS[t])
                    if p is None and t > 0:
                        p = _mean_tier_price(tier_items, TIER_KEYS[t - 1])
                    if p is not None:
                        totals[t] += p
            return totals.get(tier_idx, Decimal("0.00"))

        # ---- One-time per-person fees -----------------------------------------
        permits = self.session.exec(
            select(Permit).where(Permit.destination_id == destination.id)
        ).all()
        entry_rows = self.session.exec(
            select(EntryFee)
            .join(Attraction)
            .where(Attraction.destination_id == destination.id)
        ).all()

        fee_parts: list[dict] = []
        permit = _pick_by_category(permits, fee_category)
        if permit:
            fee_parts.append(
                {"name": permit.permit_type or "Permit", "category": _category_value(permit), "price": float(permit.price or 0)}
            )
        entry = _pick_by_category(entry_rows, fee_category)
        if entry:
            fee_parts.append(
                {"name": "Entry fee", "category": _category_value(entry), "price": float(entry.price or 0)}
            )
        one_time_per_person = Decimal(str(sum(p["price"] for p in fee_parts)))

        return {
            "destination": destination,
            "accom_price": accom_price,
            "food_daily": food_daily,
            "one_time_per_person": one_time_per_person,
            "fee_parts": fee_parts,
        }

    def estimate(
        self,
        destination_id,
        days: int = 7,
        fee_category: str = "Foreign",
    ) -> dict:
        """Per-destination average budget guide.

        Uses the standard tier of the shared cost model (food + a room/night for
        one person) plus one-time permits/entry fees, so the "average budget"
        varies by destination based on its real seeded prices.
        """
        model = self._cost_model(destination_id, fee_category)
        destination = model["destination"]
        accom_price = model["accom_price"]
        food_daily = model["food_daily"]
        one_time_per_person = model["one_time_per_person"]

        def per_person_day(tier_idx: int) -> Decimal:
            return food_daily(tier_idx) + accom_price(tier_idx)

        minimum_daily = per_person_day(0)
        average_daily = per_person_day(1)
        minimum_total = minimum_daily * days + one_time_per_person
        average_total = average_daily * days + one_time_per_person

        return {
            "destination_id": destination.id,
            "destination_name": destination.name,
            "fee_category": fee_category,
            "days": days,
            "per_person_per_day": float(average_daily),
            "minimum_per_person_per_day": float(minimum_daily),
            "one_time_fees_per_person": float(one_time_per_person),
            "estimated_total_per_person": float(
                average_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
            "minimum_total_per_person": float(
                minimum_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
            "method": "Standard-tier daily food + accommodation for one person, "
            "plus one-time permits/entry fees",
        }

    def optimize(
        self,
        destination_id,
        total_budget: float,
        party_size: int = 1,
        days: int = 1,
        fee_category: str = "Foreign",
    ) -> dict:
        model = self._cost_model(destination_id, fee_category)
        destination = model["destination"]
        accom_price = model["accom_price"]
        food_daily = model["food_daily"]
        one_time_per_person = model["one_time_per_person"]
        fee_parts = model["fee_parts"]

        budget = Decimal(str(total_budget))

        def daily_total(food_idx: int, accom_idx: int) -> Decimal:
            return food_daily(food_idx) * party_size + accom_price(accom_idx)

        # ---- Feasibility (all-budget plan) ------------------------------------
        plan = [{"food": 0, "accom": 0} for _ in range(days)]
        base_daily = daily_total(0, 0)
        minimum_budget = base_daily * days + one_time_per_person * party_size

        deficit = None
        if minimum_budget > budget:
            deficit = float((minimum_budget - budget).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        # ---- Greedy comfort upgrades -------------------------------------------
        surplus = budget - minimum_budget
        while surplus > 0:
            best = None  # (delta, day, component)
            for day in range(days):
                for comp in ("food", "accom"):
                    idx = plan[day][comp]
                    if idx >= 2:
                        continue
                    delta = Decimal("0.00")
                    if comp == "food":
                        delta = (food_daily(idx + 1) - food_daily(idx)) * party_size
                    else:
                        delta = accom_price(idx + 1) - accom_price(idx)
                    if delta > 0 and delta <= surplus and (best is None or delta < best[0]):
                        best = (delta, day, comp)
            if best is None:
                break
            delta, day, comp = best
            plan[day][comp] += 1
            surplus -= delta

        # ---- Build result -------------------------------------------------------
        daily_plan = []
        accommodation_total = Decimal("0.00")
        food_total = Decimal("0.00")
        comfort_points = 0
        for i in range(days):
            f_idx, a_idx = plan[i]["food"], plan[i]["accom"]
            food_cost = food_daily(f_idx) * party_size
            accom_cost = accom_price(a_idx)
            accommodation_total += accom_cost
            food_total += food_cost
            comfort_points += TIER_RANK[TIER_KEYS[f_idx]] + TIER_RANK[TIER_KEYS[a_idx]]
            daily_plan.append(
                {
                    "day": i + 1,
                    "food_tier": TIER_KEYS[f_idx],
                    "food_cost": float(food_cost),
                    "accommodation_tier": TIER_KEYS[a_idx],
                    "accommodation_cost": float(accom_cost),
                    "day_total": float(food_cost + accom_cost),
                }
            )

        fees_total = one_time_per_person * party_size
        grand_total = accommodation_total + food_total + fees_total
        per_person = (grand_total / party_size) if party_size else Decimal("0.00")

        return {
            "feasible": minimum_budget <= budget,
            "destination_id": destination.id,
            "destination_name": destination.name,
            "party_size": party_size,
            "days": days,
            "method": "Greedy tier allocation (bounded knapsack: cheapest comfort upgrade per bravery)",
            "minimum_budget": float(minimum_budget),
            "accommodation_total": float(accommodation_total),
            "food_total": float(food_total),
            "fees_total": float(fees_total),
            "grand_total": float(grand_total),
            "total_budget": float(budget),
            "surplus": float((budget - grand_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "deficit": deficit,
            "per_person_total": float(per_person),
            "avg_daily_per_person": float(
                (per_person / days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ) if days else 0.0,
            "comfort_score": round(comfort_points / (days * 6), 4) if days else 0.0,
            "daily_plan": daily_plan,
            "one_time_fees": fee_parts,
        }