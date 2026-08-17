from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "test@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    payload = {
        "display_name": "Test User",
        "email": "duplicate@example.com",
        "password": "Testing123!",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "An account with this email already exists"
    )


def test_register_normalizes_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "TEST@EXAMPLE.COM",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"


def test_register_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "not-an-email",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "test@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_register_invalid_display_name(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "   ",
            "email": "test@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 422



def test_registration_hashes_password(client, db):
    plain_password = "Testing123!"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "security@example.com",
            "password": plain_password,
        },
    )

    assert response.status_code == 201

    user = db.scalar(
        select(User).where(User.email == "security@example.com")
    )

    assert user is not None
    assert user.password_hash != plain_password
    assert verify_password(plain_password, user.password_hash) is True