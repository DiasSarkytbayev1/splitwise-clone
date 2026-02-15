"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import get_db
from app.main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop tables for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_new_user():
    """Test registering a new user."""
    response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["name"] == "John Doe"
    assert data["user"]["email"] == "john@example.com"
    assert "id" in data["user"]
    assert "created_at" in data["user"]
    assert "password" not in data["user"]


def test_register_duplicate_email():
    """Test that registering with duplicate email fails."""
    # Register first user
    client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )

    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "john@example.com",
            "password": "differentpassword",
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_login_success():
    """Test successful login."""
    # Register a user first
    client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )

    # Login with correct credentials
    response = client.post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "john@example.com"


def test_login_wrong_password():
    """Test login with incorrect password."""
    # Register a user
    client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "correctpassword",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword",
        },
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_me_authenticated():
    """Test getting current user profile with valid token."""
    # Register and get token
    register_response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # Get current user profile
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_me_no_token():
    """Test that /me endpoint fails without token."""
    response = client.get("/auth/me")

    assert response.status_code == 403  # FastAPI returns 403 when security scheme is not satisfied


def test_get_me_invalid_token():
    """Test that /me endpoint fails with invalid token."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token-here"},
    )

    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_token_persistence():
    """Test that the same token can be used multiple times."""
    # Register and get token
    register_response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # Use token multiple times
    for _ in range(3):
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "john@example.com"


def test_register_with_invite_group():
    """Test registering with an invite group ID."""
    # This test verifies the endpoint accepts the parameter
    # Note: In a real scenario, you'd need to create a group first
    response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
            "invite_group_id": "550e8400-e29b-41d4-a716-446655440000",
        },
    )

    # Should succeed (group joining will be skipped if group doesn't exist)
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_login_with_invite_group():
    """Test login with an invite group ID."""
    # Register first
    client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )

    # Login with invite group
    response = client.post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "password123",
            "invite_group_id": "550e8400-e29b-41d4-a716-446655440000",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
