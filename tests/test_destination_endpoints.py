"""Tests for destination creation: month-validated best_time + required photo uploads."""

import io
import json
import os

from app.services.photo_service import UPLOAD_DIR


def _payload(name="Test Dest", best_time=None, **extra):
    base = {
        "name": name,
        "category": "attraction",
        "description": "A test destination",
        "best_time": best_time if best_time is not None else ["January"],
        "permit_required": False,
        "address": {
            "province": "Bagmati", "district": "Kathmandu", "place": "Kathmandu",
            "latitude": 27.71, "longitude": 85.32, "altitude": 1400,
        },
    }
    base.update(extra)
    return base


def _files(n=1):
    return [("files", (f"img_{i}.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")) for i in range(n)]


def _cleanup(image_url):
    filepath = os.path.join(UPLOAD_DIR, os.path.basename(image_url))
    if os.path.exists(filepath):
        os.remove(filepath)


class TestDestinationCreate:
    def test_create_with_photo(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload())},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        dest = resp.json()["destination"]
        assert dest["best_time"] == ["January"]
        assert len(dest["photos"]) == 1
        assert dest["photos"][0]["image_url"].startswith("/uploads/")
        _cleanup(dest["photos"][0]["image_url"])

    def test_create_without_photo_fails(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload())},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_create_non_admin_fails(self, client, user_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload())},
            files=_files(),
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_create_invalid_month_fails(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(best_time=["Spring"]))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_create_duplicate_months_fails(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(best_time=["January", "January"]))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_create_empty_best_time_fails(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(best_time=[]))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_create_normalizes_month_case(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(best_time=["march", "APRIL"]))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        dest = resp.json()["destination"]
        assert dest["best_time"] == ["March", "April"]
        _cleanup(dest["photos"][0]["image_url"])

    def test_create_with_bad_file_type_fails(self, client, admin_token):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload())},
            files=[("files", ("evil.txt", io.BytesIO(b"x"), "text/plain"))],
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400


class TestUpdateTrekWithReferencedRoute:
    def test_update_trek_keeps_route_referencing_user_trip(self, client, admin_token, session):
        from app.core.auth import create_access_token
        from app.core.security import hash_password
        from app.models import User, UserTrip
        from app.models.user_model import PaceType, BudgetType

        payload = _payload(
            name="Annapurna Base Camp Trek", category="trek",
            trekking_routes=[{
                "route_name": "ABC Trail", "difficulty": "moderate",
                "total_distance_km": 110, "recommended_days": 10, "max_altitude": 4130,
            }],
        )
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        dest = resp.json()["destination"]
        route_id = dest["trekking_routes"][0]["id"]

        traveler = User(
            name="Traveler", email="traveler@test.com", password=hash_password("pass"),
            role="traveler", nationality="USA", phone="+977-9898989898",
        )
        session.add(traveler)
        session.commit()
        session.refresh(traveler)

        trip = UserTrip(
            user_id=traveler.id, destination_id=dest["id"], route_id=route_id,
            pace_type=PaceType.normal, budget_type=BudgetType.standard,
        )
        session.add(trip)
        session.commit()

        base = {
            "name": "Annapurna Base Camp Trek", "category": "trek", "description": "Updated description",
            "best_time": dest["best_time"], "permit_required": dest["permit_required"],
            "address": {k: v for k, v in dest["address"].items() if k != "id"},
            "trekking_routes": [{
                "route_name": "ABC Trail Updated", "difficulty": "hard",
                "total_distance_km": 120, "recommended_days": 12, "max_altitude": 4130,
            }],
        }
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(base)},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text
        _cleanup(resp.json()["destination"]["photos"][0]["image_url"])


class TestRoutePoints:
    def _create(self, client, admin_token, **extra):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(**extra))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        return resp.json()["destination"]

    @staticmethod
    def _update_payload(name="Updated Dest", keep_photo_ids=None, **extra):
        payload = _payload(name=name)
        if keep_photo_ids is not None:
            payload["keep_photo_ids"] = keep_photo_ids
        payload.update(extra)
        return payload

    def test_update_basic_fields(self, client, admin_token):
        dest = self._create(client, admin_token)
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(self._update_payload("Renamed Dest"))},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["destination"]["name"] == "Renamed Dest"
        _cleanup(body["destination"]["photos"][0]["image_url"])

    def test_update_attraction_dropping_entry_fees(self, client, admin_token):
        payload = _payload(attraction={"attraction_types": ["hiking"], "opening_hours": "6 AM", "entry_fees": [
            {"category": "Nepali", "price": 100},
        ]})
        dest = self._create(client, admin_token, **payload)
        # remove entry fees entirely
        base = {
            "name": dest["name"], "category": dest["category"], "description": dest["description"],
            "best_time": dest["best_time"], "permit_required": dest["permit_required"],
            "address": {k: v for k, v in dest["address"].items() if k != "id"},
            "attraction": {"attraction_types": ["Cultural"], "opening_hours": "8 AM", "visit_duration_hours": 3},
        }
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(base)},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()["destination"]
        assert body["attraction"]["attraction_types"] == ["Cultural"]
        assert body["attraction"].get("entry_fees") == []
        _cleanup(body["photos"][0]["image_url"])

    def test_update_non_admin_fails(self, client, admin_token, user_token):
        dest = self._create(client, admin_token)
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(self._update_payload("hacked"))},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
        _cleanup(dest["photos"][0]["image_url"])

    def test_update_removes_dropped_photo(self, client, admin_token):
        dest = self._create(client, admin_token)
        photo_id = dest["photos"][0]["id"]
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(self._update_payload("x", keep_photo_ids=[]))},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["destination"]["photos"] == []

    @staticmethod
    def _point(name, seq, province="Gandaki", district="Kaski", place=None, **extra):
        point = {
            "sequence_no": seq,
            "name": name,
            "address": {
                "province": province, "district": district,
                "place": place or name, "latitude": 28.2, "longitude": 83.9, "altitude": 1000,
            },
        }
        point.update(extra)
        return point

    def test_create_trek_with_route_points(self, client, admin_token):
        payload = _payload(
            name="Annapurna Circuit Trek", category="trek",
            trekking_routes=[{
                "route_name": "Main Circuit", "difficulty": "hard",
                "total_distance_km": 230, "recommended_days": 15, "max_altitude": 5416,
                "route_points": [
                    self._point("Besisahar", 1),
                    self._point("Manang", 2, district="Manang"),
                ],
            }],
        )
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        dest = resp.json()["destination"]
        points = dest["trekking_routes"][0]["route_points"]
        assert [p["name"] for p in points] == ["Besisahar", "Manang"]
        assert points[0]["sequence_no"] == 1
        assert points[0]["address"]["province"] == "Gandaki"
        assert points[1]["address"]["district"] == "Manang"
        _cleanup(dest["photos"][0]["image_url"])

    def test_create_route_point_requires_address(self, client, admin_token):
        payload = _payload(
            name="Broken Route", category="trek",
            trekking_routes=[{
                "route_name": "Route", "difficulty": "easy",
                "route_points": [{"sequence_no": 1, "name": "No address"}],
            }],
        )
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_update_trek_replaces_route_points(self, client, admin_token):
        payload = _payload(
            name="Trek A", category="trek",
            trekking_routes=[{
                "route_name": "Trail", "difficulty": "moderate",
                "route_points": [self._point("Old Point", 1)],
            }],
        )
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        dest = resp.json()["destination"]
        dest_id = dest["id"]

        base = {
            "name": "Trek A", "category": "trek", "description": dest["description"],
            "best_time": dest["best_time"], "permit_required": dest["permit_required"],
            "address": {k: v for k, v in dest["address"].items() if k != "id"},
            "trekking_routes": [{
                "route_name": "Trail", "difficulty": "moderate",
                "route_points": [self._point("New Point", 1), self._point("Second Point", 2, district="Lamjung")],
            }],
        }
        resp = client.put(
            f"/destinations/{dest_id}",
            data={"destination": json.dumps(base)},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text
        points = resp.json()["destination"]["trekking_routes"][0]["route_points"]
        assert [p["name"] for p in points] == ["New Point", "Second Point"]
        assert points[1]["sequence_no"] == 2
        _cleanup(resp.json()["destination"]["photos"][0]["image_url"])

    def test_update_trek_clears_route_points(self, client, admin_token):
        payload = _payload(
            name="Trek B", category="trek",
            trekking_routes=[{
                "route_name": "Trail", "difficulty": "easy",
                "route_points": [self._point("Point", 1)],
            }],
        )
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        dest = resp.json()["destination"]

        base = {
            "name": "Trek B", "category": "trek", "description": dest["description"],
            "best_time": dest["best_time"], "permit_required": dest["permit_required"],
            "address": {k: v for k, v in dest["address"].items() if k != "id"},
            "trekking_routes": [{
                "route_name": "Trail", "difficulty": "easy", "route_points": [],
            }],
        }
        resp = client.put(
            f"/destinations/{dest['id']}",
            data={"destination": json.dumps(base)},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["destination"]["trekking_routes"][0]["route_points"] == []
        _cleanup(resp.json()["destination"]["photos"][0]["image_url"])


class TestDestinationDelete:
    def _create(self, client, admin_token, **extra):
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(_payload(**extra))},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["destination"]

    def _create_with_attraction(self, client, admin_token):
        payload = _payload(attraction={
            "attraction_types": ["hiking"], "opening_hours": "6 AM",
            "entry_fees": [{"category": "Nepali", "price": 100}],
        })
        resp = client.post(
            "/destinations/",
            data={"destination": json.dumps(payload)},
            files=_files(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["destination"]

    def test_delete_plain_destination(self, client, admin_token):
        dest = self._create(client, admin_token)
        resp = client.delete(
            f"/destinations/{dest['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"]

    def test_delete_destination_with_attraction_and_fees(self, client, admin_token):
        dest = self._create_with_attraction(client, admin_token)
        resp = client.delete(
            f"/destinations/{dest['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text

    def test_delete_non_admin_fails(self, client, admin_token, user_token):
        dest = self._create(client, admin_token)
        resp = client.delete(
            f"/destinations/{dest['id']}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403
        _cleanup(dest["photos"][0]["image_url"])

    def test_delete_missing_returns_404(self, client, admin_token):
        resp = client.delete(
            "/destinations/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404
