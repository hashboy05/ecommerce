"""
Shared pytest fixtures.

Each test runs against a fresh, isolated in-memory SQLite database, so tests
never touch the real ecommerce.db and never interfere with one another.
"""
import pytest

from app import create_app
from db import db


@pytest.fixture
def app():
    """A fresh application bound to an in-memory database per test."""
    app = create_app("sqlite:///:memory:")
    yield app
    with app.app_context():
        db.session.remove()


@pytest.fixture
def client(app):
    """A Flask test client for issuing requests without a running server."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register and log in a user, returning a ready-to-use auth header."""
    client.post("/register", json={"username": "tester", "password": "pw123456"})
    token = client.post(
        "/login", json={"username": "tester", "password": "pw123456"}
    ).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
