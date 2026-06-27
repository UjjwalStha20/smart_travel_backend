from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select
from sqlalchemy.orm import selectinload

from app.models import (
    Address,
    Attraction,
    Destination,
    DestinationCategory,
    EntryFee,
    RoutePoint,
    TrekkingRoute,
)
from app.schemas.destination_schema import DestinationCreate
from app.services import AddressService


class DestinationService:
    def __init__(self, session: Session):
        self.session = session

    def _destination_to_dict(self, dest: Destination) -> dict:
        data = dest.model_dump()
        data["address"] = dest.address.model_dump() if dest.address else None
        if dest.category == DestinationCategory.attraction:
            try:
                attraction = dest.attraction
            except Exception:
                attraction = None
            if attraction:
                attr_data = attraction.model_dump()
                try:
                    attr_data["entry_fees"] = [e.model_dump() for e in attraction.entry_fees]
                except Exception:
                    attr_data["entry_fees"] = []
                data["attraction"] = attr_data
            else:
                data["attraction"] = None
            data.pop("trekking_routes", None)
        else:
            data["trekking_routes"] = []
            try:
                trekking_routes = dest.trekking_routes or []
            except Exception:
                trekking_routes = []
            for tr in trekking_routes:
                tr_data = tr.model_dump()
                try:
                    tr_data["route_points"] = [rp.model_dump() for rp in tr.route_points]
                except Exception:
                    tr_data["route_points"] = []
                data["trekking_routes"].append(tr_data)
            data.pop("attraction", None)
        return data

    def _apply_filters(self, statement, category, name, description, rating_min, permit_required, province, district, place, model_class=Destination):
        if category:
            statement = statement.where(model_class.category == category)
        if name:
            statement = statement.where(model_class.name.ilike(f"%{name}%"))
        if description:
            statement = statement.where(model_class.description.ilike(f"%{description}%"))
        if rating_min is not None:
            statement = statement.where(model_class.rating >= rating_min)
        if permit_required is not None:
            statement = statement.where(model_class.permit_required == permit_required)
        has_address_filter = province or district or place
        if has_address_filter:
            statement = statement.join(model_class.address)
            if province:
                statement = statement.where(Address.province == province)
            if district:
                statement = statement.where(Address.district == district)
            if place:
                statement = statement.where(Address.place == place)
        return statement
    
    def get_destinations(
        self,
        offset: int = 0,
        limit: int = 10,
        category: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rating_min: Optional[int] = None,
        permit_required: Optional[bool] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        place: Optional[str] = None,
    ) -> dict:
        statement = select(Destination).options(
            selectinload(Destination.address),
            selectinload(Destination.attraction).selectinload(Attraction.entry_fees),
            selectinload(Destination.trekking_routes).selectinload(TrekkingRoute.route_points),
        )

        statement = self._apply_filters(statement, category, name, description, rating_min, permit_required, province, district, place)

        statement = statement.offset(offset).limit(limit)
        items = self.session.exec(statement).all()

        count_statement = select(func.count(Destination.id))
        count_statement = self._apply_filters(count_statement, category, name, description, rating_min, permit_required, province, district, place)
        total = self.session.exec(count_statement).one()
        return {"items": [self._destination_to_dict(d) for d in items], "total": total, "offset": offset, "limit": limit}
    
    def get_destination_by_id(self, destination_id: str) -> dict:
        statement = (
            select(Destination)
            .where(Destination.id == destination_id)
            .options(
                selectinload(Destination.address),
                selectinload(Destination.attraction).selectinload(Attraction.entry_fees),
                selectinload(Destination.trekking_routes).selectinload(TrekkingRoute.route_points),
            )
        )

        destination = self.session.exec(statement).first()
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        return {
            "message": "Destination retrieved successfully",
            "destination": self._destination_to_dict(destination)
        }
    
    def create_destination(self, destination_data: DestinationCreate) -> dict:
        address = AddressService(self.session).get_or_create_address(destination_data.address)

        dump = destination_data.model_dump(exclude={"address", "attraction", "trekking_routes"})
        destination = Destination(**dump, address_id=address.id)
        self.session.add(destination)
        self.session.flush()

        if destination.category == DestinationCategory.attraction and destination_data.attraction:
            attr_data = destination_data.attraction
            attr = Attraction(
                destination_id=destination.id,
                attraction_types=attr_data.attraction_types,
                opening_hours=attr_data.opening_hours,
                visit_duration_hours=attr_data.visit_duration_hours,
            )
            self.session.add(attr)
            self.session.flush()

            if attr_data.entry_fees:
                    self.session.add_all([
                        EntryFee(attraction_id=attr.id, category=fee.category, price=fee.price)
                        for fee in attr_data.entry_fees
                    ])

        elif destination.category == DestinationCategory.trek and destination_data.trekking_routes:
            for tr_data in destination_data.trekking_routes:
                tr = TrekkingRoute(
                    destination_id=destination.id,
                    route_name=tr_data.route_name,
                    difficulty=tr_data.difficulty,
                    total_distance_km=tr_data.total_distance_km,
                    recommended_days=tr_data.recommended_days,
                    max_altitude=tr_data.max_altitude,
                    description=tr_data.description,
                )
                self.session.add(tr)
                self.session.flush()

                if tr_data.route_points:
                    self.session.add_all([
                        RoutePoint(route_id=tr.id, **rp.model_dump())
                        for rp in tr_data.route_points
                    ])

        self.session.commit()
        self.session.refresh(destination)

        # reload with relationships for the response
        return self.get_destination_by_id(str(destination.id))

    def update_destination(self, destination_id: str, destination_data) -> dict:
        existing = self.session.get(Destination, destination_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Destination not found")
        address = AddressService(self.session).get_or_create_address(destination_data.address)
        dump = destination_data.model_dump(exclude={"address", "attraction", "trekking_routes"}, exclude_unset=True)
        existing.sqlmodel_update(dump)
        existing.address_id = address.id

        if destination_data.attraction and existing.category == DestinationCategory.attraction:
            if existing.attraction:
                attr = existing.attraction
                attr.attraction_types = destination_data.attraction.attraction_types
                attr.opening_hours = destination_data.attraction.opening_hours
                attr.visit_duration_hours = destination_data.attraction.visit_duration_hours
                self.session.add(attr)
            else:
                attr = Attraction(
                    destination_id=existing.id,
                    attraction_types=destination_data.attraction.attraction_types,
                    opening_hours=destination_data.attraction.opening_hours,
                    visit_duration_hours=destination_data.attraction.visit_duration_hours,
                )
                self.session.add(attr)
                self.session.flush()

        if destination_data.trekking_routes and existing.category == DestinationCategory.trek:
            for tr_data in destination_data.trekking_routes:
                tr = TrekkingRoute(
                    destination_id=existing.id,
                    route_name=tr_data.route_name,
                    difficulty=tr_data.difficulty,
                    total_distance_km=tr_data.total_distance_km,
                    recommended_days=tr_data.recommended_days,
                    max_altitude=tr_data.max_altitude,
                    description=tr_data.description,
                )
                self.session.add(tr)
                self.session.flush()
                if tr_data.route_points:
                    self.session.add_all([
                        RoutePoint(route_id=tr.id, **rp.model_dump())
                        for rp in tr_data.route_points
                    ])

        self.session.add(existing)
        self.session.commit()
        self.session.refresh(existing)
        return {"message": "Destination updated successfully", "destination": existing}

    def delete_destination(self, destination_id: str) -> dict:
        dest = self.session.get(Destination, destination_id)
        if not dest:
            raise HTTPException(status_code=404, detail="Destination not found")
        self.session.delete(dest)
        self.session.commit()
        return {"message": "Destination deleted successfully"}
