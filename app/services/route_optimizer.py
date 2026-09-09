"""Route optimization for trekking routes (open-path TSP).

Algorithm
---------
1. Build the haversine distance matrix between every pair of waypoints.
2. Baseline: the route's recorded (DB) sequence order.
3. Nearest-neighbour tour construction tried from every possible start point,
   keeping the best (deterministic tie-breaking).
4. 2-opt local search refines the tour until no improvement is possible.

Pure-Python, deterministic, no external dependencies.
"""
import math
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Address, RoutePoint, TrekkingRoute


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two coordinates."""
    earth_radius_km = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * earth_radius_km * math.asin(math.sqrt(a))


def _path_length(order: List[int], dist: List[List[float]]) -> float:
    return sum(
        dist[order[i]][order[i + 1]] for i in range(len(order) - 1)
    )


def _nearest_neighbour(start: int, dist: List[List[float]], n: int) -> List[int]:
    tour = [start]
    unvisited = {i for i in range(n) if i != start}
    while unvisited:
        last = tour[-1]
        nxt = min(unvisited, key=lambda j: (dist[last][j], j))
        tour.append(nxt)
        unvisited.remove(nxt)
    return tour


def _two_opt(tour: List[int], dist: List[List[float]]) -> List[int]:
    """2-opt local search for an open Hamiltonian path."""
    best = tour[:]
    best_len = _path_length(best, dist)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                if j - i == 1:
                    continue
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                candidate_len = _path_length(candidate, dist)
                if candidate_len < best_len - 1e-9:
                    best = candidate
                    best_len = candidate_len
                    improved = True
    return best


class RouteOptimizer:
    def __init__(self, session: Session):
        self.session = session

    def optimize(
        self,
        route_id: Optional[str] = None,
        destination_id: Optional[str] = None,
        points: Optional[list] = None,
    ) -> dict:
        route_name, source, waypoints, walking_hours = self._resolve(
            route_id, destination_id, points
        )
        n = len(waypoints)

        dist = [
            [
                haversine_km(wp["latitude"], wp["longitude"], other["latitude"], other["longitude"])
                for other in waypoints
            ]
            for wp in waypoints
        ]

        baseline = list(range(n))
        baseline_len = _path_length(baseline, dist)

        candidates = []
        for start in range(n):
            tour = _nearest_neighbour(start, dist, n)
            tour = _two_opt(tour, dist)
            candidates.append((_path_length(tour, dist), tour))
        _, best_tour = min(candidates, key=lambda c: c[0])
        best_tour = _two_opt(best_tour, dist)
        optimized_len = _path_length(best_tour, dist)

        # Never return a tour worse than the recorded order.
        if optimized_len > baseline_len:
            best_tour = baseline
            optimized_len = baseline_len

        savings_km = round(baseline_len - optimized_len, 2)
        savings_percent = round(savings_km / baseline_len * 100, 2) if baseline_len else 0.0

        optimized_order = []
        cumulative = 0.0
        for seq, idx in enumerate(best_tour):
            stop = waypoints[idx]
            leg = 0.0 if seq == 0 else dist[best_tour[seq - 1]][idx]
            cumulative += leg
            optimized_order.append(
                {
                    "sequence": seq + 1,
                    "name": stop["name"],
                    "distance_from_previous_km": round(leg, 2),
                    "cumulative_km": round(cumulative, 2),
                    "recorded_km": stop.get("recorded_km"),
                    "overnight": stop.get("overnight", False),
                }
            )

        return {
            "route_name": route_name,
            "source": source,
            "method": "Nearest-neighbour construction + 2-opt local search (open-path TSP)",
            "stops": n,
            "original_order": [waypoints[i]["name"] for i in baseline],
            "optimized_order": optimized_order,
            "original_total_km": round(baseline_len, 2),
            "optimized_total_km": round(optimized_len, 2),
            "savings_km": savings_km,
            "savings_percent": savings_percent,
            "total_walking_hours": round(walking_hours, 2) if walking_hours is not None else None,
        }

    def _resolve(self, route_id, destination_id, points):
        """Return (route_name, source, waypoints, walking_hours)."""
        if points:
            def _field(p, name, default=None):
                if isinstance(p, dict):
                    return p.get(name, default)
                return getattr(p, name, default)

            waypoints = [
                {
                    "name": _field(p, "name"),
                    "latitude": _field(p, "latitude"),
                    "longitude": _field(p, "longitude"),
                    "recorded_km": _field(p, "recorded_km"),
                    "overnight": _field(p, "overnight", False),
                }
                for p in points
            ]
            walking_hours = None
            return "Custom route", "custom", waypoints, walking_hours

        route = None
        if route_id:
            route = self.session.get(TrekkingRoute, UUID(str(route_id)))
            if not route:
                raise HTTPException(status_code=404, detail="Trekking route not found")
        elif destination_id:
            routes = self.session.exec(
                select(TrekkingRoute).where(
                    TrekkingRoute.destination_id == UUID(str(destination_id))
                )
            ).all()
            if not routes:
                raise HTTPException(status_code=404, detail="No trekking routes found for destination")
            route = max(
                routes,
                key=lambda r: len(
                    self.session.exec(
                        select(RoutePoint).where(RoutePoint.route_id == r.id)
                    ).all()
                ),
            )

        route_points = self.session.exec(
            select(RoutePoint)
            .where(RoutePoint.route_id == route.id)
            .order_by(RoutePoint.sequence_no)
        ).all()
        if len(route_points) < 2:
            raise HTTPException(
                status_code=422,
                detail="At least two route points with GPS coordinates are required",
            )

        waypoints = []
        walking_hours = 0.0
        has_hours = True
        for rp in route_points:
            address = self.session.get(Address, rp.address_id) if rp.address_id else None
            if not address or address.latitude is None or address.longitude is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Route point '{rp.name}' is missing GPS coordinates in its address data",
                )
            waypoints.append(
                {
                    "name": rp.name,
                    "latitude": address.latitude,
                    "longitude": address.longitude,
                    "recorded_km": float(rp.distance_from_previous_km) if rp.distance_from_previous_km is not None else None,
                    "overnight": rp.overnight_stop,
                }
            )
            if rp.walking_hours_from_previous is not None:
                walking_hours += float(rp.walking_hours_from_previous)
            else:
                has_hours = False

        return route.route_name, "route", waypoints, walking_hours if has_hours else None