"""Tests for auth endpoints."""


def test_register(client):
    resp = client.post("/auth/register", json={
        "name": "NewUser", "email": "new@test.com", "password": "pass123",
        "nationality": "Nepal", "phone": "+977-9800000100",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, admin_token):
    resp = client.post("/auth/register", json={
        "name": "Admin", "email": "admin@test.com", "password": "admin123",
        "nationality": "Nepal", "phone": "+977-9800000001",
    })
    assert resp.status_code == 409


def test_login(client, user_token):
    resp = client.post("/auth/login", json={
        "email": "user@test.com", "password": "user123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post("/auth/login", json={
        "email": "user@test.com", "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_me(client, user_token):
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


def test_me_unauthorized(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_update_me(client, user_token):
    resp = client.patch(
        "/auth/me",
        json={"name": "Updated User", "phone": "+977-9800000009", "nationality": "Japan"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated User"
    assert data["phone"] == "+977-9800000009"
    assert data["nationality"] == "Japan"
    assert data["email"] == "user@test.com"


def test_update_me_unauthorized(client):
    resp = client.patch("/auth/me", json={"name": "Hacker"})
    assert resp.status_code == 401
