from sqlalchemy import select

from fastapi import Depends

from app.core.auth import get_current_user
from app.main import app
from app.models.user import User
from app.core.security import verify_password
from app.models.user import User
from app.core.config import settings

import jwt


@app.get("/test/protected")
def protected_test_endpoint(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
    }


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


def register_user(
    client,
    email="login@example.com",
    password="Testing123!",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": email,
            "password": password,
        },
    )


def test_login_success(client):
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_wrong_password(client):
    register_user(client)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_normalizes_email(client):
    register_user(client, email="login@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "LOGIN@EXAMPLE.COM",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 200


def test_access_token_contains_user_id(client):
    register_response = register_user(
        client,
        email="jwt@example.com",
    )

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "jwt@example.com",
            "password": "Testing123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == user_id
    assert "exp" in payload


def test_valid_token_authenticates_user(client):
    register_response = register_user(
        client,
        email="protected@example.com",
    )

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "protected@example.com",
            "password": "Testing123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id
    assert response.json()["email"] == "protected@example.com"


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/test/protected",
        headers={
            "Authorization": "Bearer this.is.not.a.valid.jwt",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_protected_endpoint_requires_token(client):
    response = client.get("/test/protected")

    assert response.status_code in (401, 403)




