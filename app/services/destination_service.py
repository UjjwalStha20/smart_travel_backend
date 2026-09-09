import os
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, func, select
from sqlalchemy.orm import selectinload

from app.models import (
    Address,
    Attraction,
    Destination,
    DestinationCategory,
    DestinationItinerary,
    EntryFee,
    HikeDetails,
    Itinerary,
    MountainDetails,
    NatureDetails,
    Permit,
    Photo,
    Review,
    RoutePoint,
    SavedDestination,
    TrekDetails,
    TrekkingRoute,
    User,
    UserTrip,
)
from app.schemas.destination_schema import DestinationCreate
from app.services import AddressService
from app.services.photo_service import PhotoService, UPLOAD_DIR

ATTRACTION_LIKE_CATEGORIES = {
    DestinationCategory.attraction,
    DestinationCategory.city,
    DestinationCategory.cultural_site,
    DestinationCategory.religious_site,
    DestinationCategory.historical_site,
    DestinationCategory.wildlife,
    DestinationCategory.adventure,
    DestinationCategory.other,
}
NATURE_LIKE_CATEGORIES = {
    DestinationCategory.nature,
    DestinationCategory.lake,
    DestinationCategory.waterfall,
    DestinationCategory.viewpoint,
}


class DestinationService:
    def __init__(self, session: Session):
        self.session = session

    def _section_for_category(self, category) -> str:
        if category == DestinationCategory.trek:
            return "trek"
        if category == DestinationCategory.hike:
            return "hike"
        if category == DestinationCategory.mountain:
            return "mountain"
        if category in NATURE_LIKE_CATEGORIES:
            return "nature"
        return "attraction"

    def _detail_dict(self, obj) -> Optional[dict]:
        if obj is None:
            return None
        try:
            return obj.model_dump()
        except Exception:
            return None

    def _safe_get(self, obj, name):
        try:
            return getattr(obj, name, None)
        except Exception:
            return None

    def _destination_to_dict(self, dest: Destination) -> dict:
        data = dest.model_dump()
        data["address"] = dest.address.model_dump() if dest.address else None
        try:
            data["photos"] = [p.model_dump() for p in dest.photos]
        except Exception:
            data["photos"] = []

        data["attraction"] = None
        data["trekking_routes"] = None
        data["trek_details"] = None
        data["hike_details"] = None
        data["mountain_details"] = None
        data["nature_details"] = None
        try:
            data["destination_itineraries"] = [
                it.model_dump() for it in (dest.destination_itineraries or [])
            ]
        except Exception:
            data["destination_itineraries"] = []

        section = self._section_for_category(dest.category)

        if section == "attraction":
            attraction = self._safe_get(dest, "attraction")
            if attraction:
                attr_data = attraction.model_dump()
                try:
                    attr_data["entry_fees"] = [e.model_dump() for e in attraction.entry_fees]
                except Exception:
                    attr_data["entry_fees"] = []
                data["attraction"] = attr_data
        elif section == "trek":
            data["trek_details"] = self._detail_dict(self._safe_get(dest, "trek_details"))
            data["trekking_routes"] = []
            try:
                trekking_routes = dest.trekking_routes or []
            except Exception:
                trekking_routes = []
            for tr in trekking_routes:
                tr_data = tr.model_dump()
                try:
                    points = []
                    for rp in tr.route_points:
                        rp_data = rp.model_dump()
                        try:
                            rp_data["address"] = rp.address.model_dump()
                        except Exception:
                            rp_data["address"] = None
                        points.append(rp_data)
                    tr_data["route_points"] = points
                except Exception:
                    tr_data["route_points"] = []
                data["trekking_routes"].append(tr_data)
        elif section == "hike":
            data["hike_details"] = self._detail_dict(self._safe_get(dest, "hike_details"))
        elif section == "mountain":
            data["mountain_details"] = self._detail_dict(self._safe_get(dest, "mountain_details"))
        elif section == "nature":
            data["nature_details"] = self._detail_dict(self._safe_get(dest, "nature_details"))
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
            selectinload(Destination.trek_details),
            selectinload(Destination.hike_details),
            selectinload(Destination.mountain_details),
            selectinload(Destination.nature_details),
            selectinload(Destination.photos),
        )

        statement = self._apply_filters(statement, category, name, description, rating_min, permit_required, province, district, place)

        statement = statement.offset(offset).limit(limit)
        items = self.session.exec(statement).all()

        count_statement = select(func.count(Destination.id))
        count_statement = self._apply_filters(count_statement, category, name, description, rating_min, permit_required, province, district, place)
        total = self.session.exec(count_statement).one()
        return {"items": [self._destination_to_dict(d) for d in items], "total": total, "offset": offset, "limit": limit}
    
    def get_destinations_stats(self) -> dict:
        total = self.session.exec(select(func.count(Destination.id))).one()

        avg_rating_row = self.session.exec(
            select(func.avg(Destination.rating)).where(Destination.rating.isnot(None))
        ).one()
        avg_rating = round(float(avg_rating_row), 1) if avg_rating_row else 0

        provinces_row = self.session.exec(
            select(func.count(func.distinct(Address.province)))
            .select_from(Destination)
            .join(Address)
        ).one()

        travelers = self.session.exec(
            select(func.count(User.id)).where(User.role == "traveler")
        ).one()

        return {
            "total_destinations": total,
            "total_provinces": provinces_row,
            "avg_rating": avg_rating,
            "total_travelers": travelers,
        }

    def get_destination_by_id(self, destination_id: str) -> dict:
        statement = (
            select(Destination)
            .where(Destination.id == destination_id)
            .options(
                selectinload(Destination.address),
                selectinload(Destination.attraction).selectinload(Attraction.entry_fees),
                selectinload(Destination.trekking_routes).selectinload(TrekkingRoute.route_points),
                selectinload(Destination.trek_details),
                selectinload(Destination.hike_details),
                selectinload(Destination.mountain_details),
                selectinload(Destination.nature_details),
                selectinload(Destination.photos),
            )
        )

        destination = self.session.exec(statement).first()
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        return {
            "message": "Destination retrieved successfully",
            "destination": self._destination_to_dict(destination)
        }
    
    def create_destination(
        self,
        destination_data: DestinationCreate,
        photo_uploads: Optional[List[tuple[str, bytes]]] = None,
        uploaded_by: Optional[UUID] = None,
        featured_file: Optional[tuple[str, bytes]] = None,
    ) -> dict:
        address = AddressService(self.session).get_or_create_address(destination_data.address)

        dump = destination_data.model_dump(
            exclude={
                "address", "attraction", "trekking_routes", "trek_details",
                "hike_details", "mountain_details", "nature_details", "itinerary",
            }
        )
        destination = Destination(**dump, address_id=address.id)
        self.session.add(destination)
        self.session.flush()

        section = self._section_for_category(destination.category)

        if section == "attraction" and destination_data.attraction:
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

        elif section == "trek":
            if destination_data.trek_details is not None:
                row = TrekDetails(destination_id=destination.id, **destination_data.trek_details.model_dump())
                self.session.add(row)
            if destination_data.trekking_routes:
                self._create_trekking_routes(destination, destination_data.trekking_routes)

        elif section == "hike" and destination_data.hike_details is not None:
            row = HikeDetails(destination_id=destination.id, **destination_data.hike_details.model_dump())
            self.session.add(row)

        elif section == "mountain" and destination_data.mountain_details is not None:
            row = MountainDetails(destination_id=destination.id, **destination_data.mountain_details.model_dump())
            self.session.add(row)

        elif section == "nature" and destination_data.nature_details is not None:
            row = NatureDetails(destination_id=destination.id, **destination_data.nature_details.model_dump())
            self.session.add(row)

        if destination_data.itinerary:
            self._create_itinerary(destination, destination_data.itinerary)

        self.session.commit()
        self.session.refresh(destination)

        if featured_file and uploaded_by is not None:
            filename, content = featured_file
            photo_service = PhotoService(self.session)
            photo_service.create_photo_from_upload(
                destination_id=destination.id, user_id=uploaded_by,
                filename=filename, content=content, is_featured=True,
            )

        if photo_uploads and uploaded_by is not None:
            photo_service = PhotoService(self.session)
            for filename, content in photo_uploads:
                photo_service.create_photo_from_upload(
                    destination_id=destination.id, user_id=uploaded_by,
                    filename=filename, content=content,
                )

        # reload with relationships for the response
        return self.get_destination_by_id(str(destination.id))

    def _create_trekking_routes(self, destination: Destination, routes_data) -> None:
        for tr_data in routes_data:
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

            if tr_data.route_points is not None:
                self._replace_route_points(tr, tr_data.route_points)

    def _create_itinerary(self, destination: Destination, itinerary_data) -> None:
        self.session.add_all([
            DestinationItinerary(
                destination_id=destination.id,
                day_number=d.day_number,
                title=d.title,
                start_location=d.start_location,
                end_location=d.end_location,
                overnight_location=d.overnight_location,
                estimated_walking_hours=d.estimated_walking_hours,
                notes=d.notes,
            )
            for d in itinerary_data
        ])
        self.session.flush()

    def _replace_attraction(self, existing: Destination, attr_data) -> None:
        if existing.attraction:
            attr = existing.attraction
            attr.attraction_types = attr_data.attraction_types
            attr.opening_hours = attr_data.opening_hours
            attr.visit_duration_hours = attr_data.visit_duration_hours
            fees = list(attr.entry_fees or [])
            for fee in fees:
                self.session.delete(fee)
            attr.entry_fees = []
            self.session.flush()
        else:
            attr = Attraction(
                destination_id=existing.id,
                attraction_types=attr_data.attraction_types,
                opening_hours=attr_data.opening_hours,
                visit_duration_hours=attr_data.visit_duration_hours,
            )
            self.session.add(attr)
            self.session.flush()

        if attr_data.entry_fees:
            self.session.add_all(
                EntryFee(attraction_id=attr.id, category=f.category, price=f.price)
                for f in attr_data.entry_fees
            )

    def _replace_route_points(self, route: TrekkingRoute, points_data) -> None:
        for rp in list(route.route_points or []):
            self.session.delete(rp)
        route.route_points = []
        self.session.flush()

        created = []
        for rp in points_data:
            address_id = getattr(rp, "address_id", None)
            if getattr(rp, "address", None):
                address = AddressService(self.session).get_or_create_address(rp.address)
                address_id = address.id
            if not address_id:
                raise HTTPException(status_code=400, detail="Route point requires an address")
            point = RoutePoint(
                route_id=route.id,
                sequence_no=rp.sequence_no,
                name=rp.name,
                distance_from_previous_km=rp.distance_from_previous_km,
                walking_hours_from_previous=rp.walking_hours_from_previous,
                overnight_stop=rp.overnight_stop,
                description=rp.description,
                address_id=address_id,
                accommodation_id=getattr(rp, "accommodation_id", None),
                food_cost_id=getattr(rp, "food_cost_id", None),
            )
            self.session.add(point)
            created.append(point)
        self.session.flush()
        route.route_points = created

    def _replace_trekking_routes(self, existing: Destination, routes_data) -> None:
        existing_routes = list(existing.trekking_routes or [])
        referenced_ids = set()
        if existing_routes:
            stmt = select(UserTrip.route_id).where(
                UserTrip.route_id.in_([r.id for r in existing_routes])
            )
            referenced_ids = {row for row in self.session.exec(stmt).all()}

        # update existing routes in place so user trips referencing them stay intact
        for i, tr_data in enumerate(routes_data):
            if i < len(existing_routes):
                route = existing_routes[i]
                route.route_name = tr_data.route_name
                route.difficulty = tr_data.difficulty
                route.total_distance_km = tr_data.total_distance_km
                route.recommended_days = tr_data.recommended_days
                route.max_altitude = tr_data.max_altitude
                route.description = tr_data.description
                self.session.add(route)
                if tr_data.route_points is not None:
                    self._replace_route_points(route, tr_data.route_points)
            else:
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
                if tr_data.route_points is not None:
                    self._replace_route_points(tr, tr_data.route_points)

        # remove only excess routes that are NOT referenced by any user trip
        for route in existing_routes[len(routes_data):]:
            if route.id in referenced_ids:
                continue
            for rp in list(route.route_points or []):
                self.session.delete(rp)
            route.route_points = []
            self.session.delete(route)
        self.session.flush()

    def _sync_photos(
        self,
        existing: Destination,
        keep_photo_ids: Optional[list] = None,
        photo_uploads: Optional[List[tuple[str, bytes]]] = None,
        uploaded_by: Optional[UUID] = None,
        featured_photo_id: Optional[str] = None,
        featured_file: Optional[tuple[str, bytes]] = None,
    ) -> None:
        if keep_photo_ids is not None:
            keep = {str(i) for i in keep_photo_ids}
            photos = list(existing.photos or [])
            for photo in photos:
                if str(photo.id) not in keep:
                    if photo.image_url and photo.image_url.startswith("/uploads/"):
                        filepath = os.path.join(UPLOAD_DIR, os.path.basename(photo.image_url))
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    existing.photos.remove(photo)
                    self.session.delete(photo)
            self.session.flush()

        # normalize existing photos: exactly one featured stays featured
        if featured_photo_id is not None:
            for photo in list(existing.photos or []):
                photo.is_featured = str(photo.id) == str(featured_photo_id)
            self.session.flush()

        if photo_uploads and uploaded_by is not None:
            photo_service = PhotoService(self.session)
            for filename, content in photo_uploads:
                photo_service.create_photo_from_upload(
                    destination_id=existing.id, user_id=uploaded_by,
                    filename=filename, content=content,
                )

        if featured_file and uploaded_by is not None:
            for photo in list(existing.photos or []):
                photo.is_featured = False
            self.session.flush()
            filename, content = featured_file
            photo_service = PhotoService(self.session)
            photo_service.create_photo_from_upload(
                destination_id=existing.id, user_id=uploaded_by,
                filename=filename, content=content, is_featured=True,
            )

    def _replace_type_details(self, existing: Destination, section: str, data) -> None:
        if data is None:
            return
        model_map = {
            "trek": (TrekDetails, "trek_details"),
            "hike": (HikeDetails, "hike_details"),
            "mountain": (MountainDetails, "mountain_details"),
            "nature": (NatureDetails, "nature_details"),
        }
        model_cls, attr = model_map[section]
        payload = data.model_dump(exclude_unset=True)
        current = self._safe_get(existing, attr)
        if current is not None:
            current.sqlmodel_update(payload)
            self.session.add(current)
        else:
            row = model_cls(destination_id=existing.id, **payload)
            self.session.add(row)
            setattr(existing, attr, row)
        self.session.flush()

    def _replace_itinerary(self, existing: Destination, itinerary_data) -> None:
        for it in list(existing.destination_itineraries or []):
            self.session.delete(it)
        existing.destination_itineraries = []
        self.session.flush()
        if itinerary_data:
            self._create_itinerary(existing, itinerary_data)

    def update_destination(
        self,
        destination_id: str,
        destination_data,
        photo_uploads: Optional[List[tuple[str, bytes]]] = None,
        uploaded_by: Optional[UUID] = None,
        featured_file: Optional[tuple[str, bytes]] = None,
    ) -> dict:
        existing = self.session.get(Destination, destination_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Destination not found")
        address = AddressService(self.session).get_or_create_address(destination_data.address)
        dump = destination_data.model_dump(
            exclude={
                "address", "attraction", "trekking_routes", "trek_details",
                "hike_details", "mountain_details", "nature_details", "itinerary",
                "keep_photo_ids", "featured_photo_id",
            },
            exclude_unset=True,
        )
        existing.sqlmodel_update(dump)
        existing.address_id = address.id

        section = self._section_for_category(existing.category)

        if section == "attraction" and destination_data.attraction is not None:
            self._replace_attraction(existing, destination_data.attraction)

        if section == "trek":
            if "trek_details" in destination_data.model_fields_set:
                self._replace_type_details(existing, "trek", destination_data.trek_details)
            if destination_data.trekking_routes is not None:
                self._replace_trekking_routes(existing, destination_data.trekking_routes)

        if section == "hike" and "hike_details" in destination_data.model_fields_set:
            self._replace_type_details(existing, "hike", destination_data.hike_details)

        if section == "mountain" and "mountain_details" in destination_data.model_fields_set:
            self._replace_type_details(existing, "mountain", destination_data.mountain_details)

        if section == "nature" and "nature_details" in destination_data.model_fields_set:
            self._replace_type_details(existing, "nature", destination_data.nature_details)

        if "itinerary" in destination_data.model_fields_set:
            self._replace_itinerary(existing, destination_data.itinerary)

        self._sync_photos(
            existing,
            keep_photo_ids=destination_data.keep_photo_ids,
            photo_uploads=photo_uploads,
            uploaded_by=uploaded_by,
            featured_photo_id=(
                str(destination_data.featured_photo_id)
                if getattr(destination_data, "featured_photo_id", None) is not None
                else None
            ),
            featured_file=featured_file,
        )

        self.session.commit()
        self.session.refresh(existing)
        return self.get_destination_by_id(str(existing.id))

    def delete_destination(self, destination_id: str) -> dict:
        dest = self.session.get(Destination, destination_id)
        if not dest:
            raise HTTPException(status_code=404, detail="Destination not found")

        # photos (remove files + rows)
        for photo in list(dest.photos or []):
            if photo.image_url and photo.image_url.startswith("/uploads/"):
                filepath = os.path.join(UPLOAD_DIR, os.path.basename(photo.image_url))
                if os.path.exists(filepath):
                    os.remove(filepath)
            self.session.delete(photo)
        dest.photos = []

        # attraction -> entry fees
        if dest.attraction:
            attr = dest.attraction
            for fee in list(attr.entry_fees or []):
                self.session.delete(fee)
            attr.entry_fees = []
            self.session.delete(attr)
        dest.attraction = None

        # type-specific detail rows
        for row, attr in [
            (self._safe_get(dest, "trek_details"), "trek_details"),
            (self._safe_get(dest, "hike_details"), "hike_details"),
            (self._safe_get(dest, "mountain_details"), "mountain_details"),
            (self._safe_get(dest, "nature_details"), "nature_details"),
        ]:
            if row is not None:
                self.session.delete(row)
                setattr(dest, attr, None)

        # user trips -> itineraries (must go before trekking routes: trips reference route_id)
        for trip in list(dest.user_trips or []):
            for it in list(trip.itineraries or []):
                self.session.delete(it)
            trip.itineraries = []
            self.session.delete(trip)
        dest.user_trips = []

        # trekking routes -> route points
        for route in list(dest.trekking_routes or []):
            for rp in list(route.route_points or []):
                self.session.delete(rp)
            route.route_points = []
            self.session.delete(route)
        dest.trekking_routes = []

        # leaf rows referencing the destination
        for row in list(dest.permits or []):
            self.session.delete(row)
        dest.permits = []
        for row in list(dest.reviews or []):
            self.session.delete(row)
        dest.reviews = []
        for row in list(dest.saved_destinations or []):
            self.session.delete(row)
        dest.saved_destinations = []
        for row in list(dest.destination_itineraries or []):
            self.session.delete(row)
        dest.destination_itineraries = []

        self.session.flush()
        self.session.delete(dest)
        self.session.commit()
        return {"message": "Destination deleted successfully"}
