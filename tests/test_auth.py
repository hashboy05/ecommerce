"""Tests for user registration and JWT authentication."""


def test_register_returns_201_and_hides_password(client):
    resp = client.post("/register", json={"username": "alice", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["username"] == "alice"
    # The password (or its hash) must never be serialized back to the client.
    assert "password" not in data


def test_register_duplicate_username_returns_409(client):
    client.post("/register", json={"username": "bob", "password": "secret123"})
    resp = client.post("/register", json={"username": "bob", "password": "secret123"})
    assert resp.status_code == 409


def test_login_returns_access_token(client):
    client.post("/register", json={"username": "carol", "password": "secret123"})
    resp = client.post("/login", json={"username": "carol", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_with_wrong_password_returns_401(client):
    client.post("/register", json={"username": "dave", "password": "secret123"})
    resp = client.post("/login", json={"username": "dave", "password": "wrong-pw"})
    assert resp.status_code == 401


def test_user_me_requires_token(client):
    assert client.get("/user/me").status_code == 401


def test_user_me_with_token_returns_profile(client, auth_headers):
    resp = client.get("/user/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "tester"
