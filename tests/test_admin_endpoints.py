"""Tests for admin-only CRUD endpoints (Address, Accommodation, EntryFee, FoodCost, Permit, RoutePoint, TrekkingRoute)."""

import pytest


class TestAddress:
    def test_list_addresses(self, client, test_addresses):
        resp = client.get("/addresses/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_get_address(self, client, test_addresses):
        addr_id = test_addresses[0].id
        resp = client.get(f"/addresses/{addr_id}")
        assert resp.status_code == 200
        assert resp.json()["place"] == "Kathmandu"

    def test_create_address_as_admin(self, client, admin_token):
        resp = client.post("/addresses/", json={
            "province": "Province 1", "district": "Sunsari", "place": "Dharan",
            "latitude": 26.82, "longitude": 87.28, "altitude": 305,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["place"] == "Dharan"

    def test_create_address_as_user_fails(self, client, user_token):
        resp = client.post("/addresses/", json={
            "province": "Province 1", "district": "Sunsari", "place": "Dharan",
            "latitude": 26.82, "longitude": 87.28, "altitude": 305,
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403

    def test_update_address_as_admin(self, client, test_addresses, admin_token):
        addr_id = test_addresses[0].id
        resp = client.put(f"/addresses/{addr_id}", json={"place": "KTM"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["place"] == "KTM"

    def test_delete_address_as_admin(self, client, test_addresses, admin_token):
        addr_id = test_addresses[0].id
        resp = client.delete(f"/addresses/{addr_id}",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code in (200, 204)

    def test_list_pagination(self, client, test_addresses):
        resp = client.get("/addresses/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2


class TestAccommodation:
    def test_list(self, client, test_accommodation):
        resp = client.get("/accommodations/")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_create_as_admin(self, client, admin_token):
        resp = client.post("/accommodations/", json={
            "budget_price": 5, "standard_price": 20, "luxury_price": 80,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201

    def test_create_as_user_fails(self, client, user_token):
        resp = client.post("/accommodations/", json={
            "budget_price": 5, "standard_price": 20, "luxury_price": 80,
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403

    def test_delete_as_admin(self, client, test_accommodation, admin_token):
        resp = client.delete(f"/accommodations/{test_accommodation.id}",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code in (200, 204)


class TestFoodCost:
    def test_list(self, client, test_food_cost):
        resp = client.get("/food_costs/")
        assert resp.status_code == 200

    def test_create_as_admin(self, client, admin_token):
        resp = client.post("/food_costs/", json={
            "budget_price": 300, "standard_price": 800, "luxury_price": 2000,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201

    def test_create_as_user_fails(self, client, user_token):
        resp = client.post("/food_costs/", json={
            "budget_price": 300, "standard_price": 800, "luxury_price": 2000,
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403


class TestPermit:
    def _create_test_destination(self, session, test_addresses):
        from app.models import Destination, DestinationCategory
        d = Destination(
            name="Permit Dest", description="Test", category=DestinationCategory.attraction,
            best_time_to_visit="Spring", address_id=test_addresses[0].id,
        )
        session.add(d)
        session.commit()
        session.refresh(d)
        return d

    def test_list_public(self, client):
        resp = client.get("/permits/")
        assert resp.status_code == 200

    def test_create_as_admin(self, client, session, test_addresses, admin_token):
        dest = self._create_test_destination(session, test_addresses)
        resp = client.post("/permits/", json={
            "destination_id": str(dest.id),
            "category": "Nepali",
            "price": 500,
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201

    def test_create_as_user_fails(self, client, session, test_addresses, user_token):
        from app.models import Destination, DestinationCategory
        d = Destination(
            name="Permit Dest 2", description="Test", category=DestinationCategory.attraction,
            best_time_to_visit="Spring", address_id=test_addresses[0].id,
        )
        session.add(d)
        session.commit()
        session.refresh(d)
        resp = client.post("/permits/", json={
            "destination_id": str(d.id),
            "category": "Foreign",
            "price": 2000,
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403
