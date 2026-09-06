"""Tests for user-owned endpoints (Review, SavedDestination, UserTrip, Itinerary, Photo)."""


class TestReview:
    def _create_test_destination(self, session, test_addresses):
        from app.models import Destination, DestinationCategory
        d = Destination(
            name="Test Destination", description="Test", category=DestinationCategory.attraction,
            best_time=["Spring"], address_id=test_addresses[0].id,
        )
        session.add(d)
        session.commit()
        session.refresh(d)
        return d

    def test_create_review(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        resp = client.post("/reviews/", json={
            "destination_id": str(dest.id), "rating": 4, "comment": "Great place!",
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 201
        assert resp.json()["rating"] == 4
        assert resp.json()["user_id"] is not None

    def test_duplicate_review_returns_409(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        payload = {"destination_id": str(dest.id), "rating": 4, "comment": "Once"}
        first = client.post("/reviews/", json=payload,
                            headers={"Authorization": f"Bearer {user_token}"})
        assert first.status_code == 201
        second = client.post("/reviews/", json=payload,
                             headers={"Authorization": f"Bearer {user_token}"})
        assert second.status_code == 409

    def test_list_reviews_public(self, client):
        resp = client.get("/reviews/")
        assert resp.status_code == 200

    def test_update_own_review(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        create_resp = client.post("/reviews/", json={
            "destination_id": str(dest.id), "rating": 3, "comment": "OK",
        }, headers={"Authorization": f"Bearer {user_token}"})
        review_id = create_resp.json()["id"]

        resp = client.put(f"/reviews/{review_id}", json={"rating": 5, "comment": "Amazing!"},
                          headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        assert resp.json()["rating"] == 5

    def test_delete_own_review(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        create_resp = client.post("/reviews/", json={
            "destination_id": str(dest.id), "rating": 3, "comment": "OK",
        }, headers={"Authorization": f"Bearer {user_token}"})
        review_id = create_resp.json()["id"]

        resp = client.delete(f"/reviews/{review_id}",
                             headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code in (200, 204)

    def test_delete_other_user_review_as_admin(self, client, session, test_addresses,
                                                user_token, admin_token):
        dest = self._create_test_destination(session, test_addresses)
        create_resp = client.post("/reviews/", json={
            "destination_id": str(dest.id), "rating": 3, "comment": "OK",
        }, headers={"Authorization": f"Bearer {user_token}"})
        review_id = create_resp.json()["id"]

        resp = client.delete(f"/reviews/{review_id}",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code in (200, 204)

    def test_delete_other_user_review_unauthorized_fails(self, client, session, test_addresses,
                                                          user_token):
        resp = client.post("/auth/register", json={
            "name": "Other", "email": "other@test.com", "password": "other123",
            "nationality": "India", "phone": "+977-9800000003",
        })
        other_token = resp.json()["access_token"]

        dest = self._create_test_destination(session, test_addresses)
        create_resp = client.post("/reviews/", json={
            "destination_id": str(dest.id), "rating": 3, "comment": "OK",
        }, headers={"Authorization": f"Bearer {other_token}"})
        review_id = create_resp.json()["id"]

        resp = client.delete(f"/reviews/{review_id}",
                             headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403


class TestSavedDestination:
    def _create_test_destination(self, session, test_addresses):
        from app.models import Destination, DestinationCategory
        d = Destination(
            name="Save Test Dest", description="Test", category=DestinationCategory.attraction,
            best_time=["Spring"], address_id=test_addresses[0].id,
        )
        session.add(d)
        session.commit()
        session.refresh(d)
        return d

    def test_create_and_list(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        resp = client.post("/saved-destinations/", json={"destination_id": str(dest.id)},
                           headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 201

        list_resp = client.get("/saved-destinations/",
                               headers={"Authorization": f"Bearer {user_token}"})
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

    def test_delete(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        create = client.post("/saved-destinations/", json={"destination_id": str(dest.id)},
                             headers={"Authorization": f"Bearer {user_token}"})
        saved_id = create.json()["id"]

        resp = client.delete(f"/saved-destinations/{saved_id}",
                             headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code in (200, 204)

    def test_duplicate_save_is_idempotent(self, client, session, test_addresses, user_token):
        dest = self._create_test_destination(session, test_addresses)
        payload = {"destination_id": str(dest.id)}
        first = client.post("/saved-destinations/", json=payload,
                            headers={"Authorization": f"Bearer {user_token}"})
        assert first.status_code == 201
        second = client.post("/saved-destinations/", json=payload,
                             headers={"Authorization": f"Bearer {user_token}"})
        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]
