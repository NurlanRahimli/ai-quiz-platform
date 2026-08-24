from sqlalchemy import select
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.services.email_service import EmailDeliveryError
from app.core.security import hash_otp, hash_password

from app.models.email_verification import EmailVerification

from app.models.user import User
from app.core.security import verify_password
from app.core.config import settings

import jwt



@patch(
    "app.api.v1.auth.send_verification_email",
    side_effect=EmailDeliveryError("SendGrid failed"),
)
def test_register_rolls_back_when_email_delivery_fails(
    mock_send_email,
    client,
    db,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Delivery Failure User",
            "email": "delivery-failure@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unable to send verification email"
    )

    user = db.scalar(
        select(User).where(
            User.email == "delivery-failure@example.com"
        )
    )
    assert user is None

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email
            == "delivery-failure@example.com"
        )
    )
    assert verification is None

    mock_send_email.assert_called_once()



@patch("app.api.v1.auth.send_verification_email")
def test_resend_preserves_verification_when_email_delivery_fails(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Resend Failure User",
                "email": "resend-failure@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email
            == "resend-failure@example.com"
        )
    )
    assert verification is not None

    verification.last_sent_at = (
        datetime.now(timezone.utc)
        - timedelta(
            seconds=settings.email_otp_resend_cooldown_seconds + 1
        )
    )
    db.commit()

    original_otp_hash = verification.otp_hash
    original_expires_at = verification.expires_at

    mock_send_email.side_effect = EmailDeliveryError(
        "SendGrid failed"
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="654321",
    ):
        response = client.post(
            "/api/v1/auth/resend-verification",
            json={
                "email": "resend-failure@example.com",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unable to send verification email"
    )

    db.refresh(verification)

    assert verification.otp_hash == original_otp_hash
    assert verification.expires_at == original_expires_at

    # The original code must still be usable.
    verify_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "resend-failure@example.com",
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 201


@patch("app.api.v1.auth.send_verification_email")
def test_register_creates_pending_email_verification(
    mock_send_email,
    client,
    db,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Test User",
            "email": "pending@example.com",
            "password": "Testing123!",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "email": "pending@example.com",
        "message": "Verification code sent",
    }

    user = db.scalar(
        select(User).where(User.email == "pending@example.com")
    )
    assert user is None

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "pending@example.com"
        )
    )

    assert verification is not None
    assert verification.display_name == "Test User"
    assert verification.password_hash != "Testing123!"
    assert verification.otp_hash
    assert verification.attempt_count == 0

    mock_send_email.assert_called_once()


@patch("app.api.v1.auth.send_verification_email")
def test_verify_email_creates_user(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Verified User",
                "email": "verified@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    user_before_verification = db.scalar(
        select(User).where(
            User.email == "verified@example.com"
        )
    )
    assert user_before_verification is None

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "verified@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "verified@example.com"
    assert data["display_name"] == "Verified User"
    assert data["is_active"] is True
    assert "id" in data
    assert "password_hash" not in data

    user = db.scalar(
        select(User).where(
            User.email == "verified@example.com"
        )
    )

    assert user is not None
    assert verify_password(
        "Testing123!",
        user.password_hash,
    )

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "verified@example.com"
        )
    )

    assert verification is None

    mock_send_email.assert_called_once()


@patch("app.api.v1.auth.send_verification_email")
def test_verify_email_rejects_invalid_otp(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Invalid OTP User",
                "email": "invalid-otp@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "invalid-otp@example.com",
            "otp": "654321",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification code"

    user = db.scalar(
        select(User).where(
            User.email == "invalid-otp@example.com"
        )
    )
    assert user is None

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "invalid-otp@example.com"
        )
    )

    assert verification is not None
    assert verification.attempt_count == 1

    mock_send_email.assert_called_once()


@patch("app.api.v1.auth.send_verification_email")
def test_verify_email_rejects_expired_otp(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Expired OTP User",
                "email": "expired-otp@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "expired-otp@example.com"
        )
    )
    assert verification is not None

    verification.expires_at = datetime.now(timezone.utc) - timedelta(
        minutes=1
    )
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "expired-otp@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Verification code has expired"

    user = db.scalar(
        select(User).where(
            User.email == "expired-otp@example.com"
        )
    )
    assert user is None


@patch("app.api.v1.auth.send_verification_email")
def test_verify_email_blocks_after_max_attempts(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Locked OTP User",
                "email": "locked-otp@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    for _ in range(settings.email_otp_max_attempts):
        response = client.post(
            "/api/v1/auth/verify-email",
            json={
                "email": "locked-otp@example.com",
                "otp": "654321",
            },
        )

        assert response.status_code == 400

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "locked-otp@example.com"
        )
    )
    assert verification is not None
    assert (
        verification.attempt_count
        == settings.email_otp_max_attempts
    )

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "locked-otp@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many verification attempts"

    user = db.scalar(
        select(User).where(
            User.email == "locked-otp@example.com"
        )
    )
    assert user is None



@patch("app.api.v1.auth.send_verification_email")
def test_resend_verification_enforces_cooldown(
    mock_send_email,
    client,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Cooldown User",
                "email": "cooldown@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "cooldown@example.com",
        },
    )

    assert response.status_code == 429
    assert "Please wait" in response.json()["detail"]
    assert "before requesting another code" in response.json()["detail"]

    # Only the original registration email should have been sent.
    assert mock_send_email.call_count == 1



@patch("app.api.v1.auth.send_verification_email")
def test_resend_verification_replaces_old_otp(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Resend User",
                "email": "resend@example.com",
                "password": "Testing123!",
            },
        )

    assert register_response.status_code == 202

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "resend@example.com"
        )
    )
    assert verification is not None

    verification.last_sent_at = (
        datetime.now(timezone.utc)
        - timedelta(
            seconds=settings.email_otp_resend_cooldown_seconds + 1
        )
    )
    db.commit()

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="654321",
    ):
        resend_response = client.post(
            "/api/v1/auth/resend-verification",
            json={
                "email": "resend@example.com",
            },
        )

    assert resend_response.status_code == 200
    assert resend_response.json() == {
        "email": "resend@example.com",
        "message": "Verification code resent",
    }

    # The original code must no longer work.
    old_code_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "resend@example.com",
            "otp": "123456",
        },
    )

    assert old_code_response.status_code == 400
    assert (
        old_code_response.json()["detail"]
        == "Invalid verification code"
    )

    # The newly generated code should work.
    new_code_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "resend@example.com",
            "otp": "654321",
        },
    )

    assert new_code_response.status_code == 201
    assert new_code_response.json()["email"] == "resend@example.com"

    assert mock_send_email.call_count == 2


@patch("app.api.v1.auth.send_verification_email")
def test_register_user_success(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Test User",
                "email": "test@example.com",
                "password": "Testing123!",
            },
        )

    assert response.status_code == 202

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["message"] == "Verification code sent"

    # Registration must not create the real account yet.
    user = db.scalar(
        select(User).where(User.email == "test@example.com")
    )
    assert user is None

    # The verification email should have been requested once.
    mock_send_email.assert_called_once_with(
        to_email="test@example.com",
        otp="123456",
    )


def test_register_duplicate_email(client):
    first_response = register_user(
        client,
        email="duplicate@example.com",
    )

    assert first_response.status_code == 201

    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Another User",
            "email": "duplicate@example.com",
            "password": "Different123!",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An account with this email already exists"
    )


@patch("app.api.v1.auth.send_verification_email")
def test_register_again_updates_pending_verification(
    mock_send_email,
    client,
    db,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        first_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Original Name",
                "email": "pending-again@example.com",
                "password": "Original123!",
            },
        )

    assert first_response.status_code == 202

    original = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "pending-again@example.com"
        )
    )
    assert original is not None

    original_id = original.id

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="654321",
    ):
        second_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Updated Name",
                "email": "pending-again@example.com",
                "password": "Updated123!",
            },
        )

    assert second_response.status_code == 202

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "pending-again@example.com"
        )
    )

    assert verification is not None
    assert verification.id == original_id
    assert verification.display_name == "Updated Name"
    assert verification.attempt_count == 0

    assert verify_password(
        "Updated123!",
        verification.password_hash,
    )

    assert not verify_password(
        "Original123!",
        verification.password_hash,
    )

    mock_send_email.assert_called_with(
        to_email="pending-again@example.com",
        otp="654321",
    )
    assert mock_send_email.call_count == 2


@patch("app.api.v1.auth.send_verification_email")
def test_register_normalizes_email(
    mock_send_email,
    client,
):
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Test User",
                "email": "TEST@EXAMPLE.COM",
                "password": "Testing123!",
            },
        )

    assert response.status_code == 202
    assert response.json()["email"] == "test@example.com"

    mock_send_email.assert_called_once_with(
        to_email="test@example.com",
        otp="123456",
    )


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


@patch("app.api.v1.auth.send_verification_email")
def test_registration_hashes_password(
    mock_send_email,
    client,
    db,
):
    plain_password = "Testing123!"

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Test User",
                "email": "security@example.com",
                "password": plain_password,
            },
        )

    assert response.status_code == 202

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.email == "security@example.com"
        )
    )

    assert verification is not None

    # Never store the registration password in plaintext.
    assert verification.password_hash != plain_password

    assert verify_password(
        plain_password,
        verification.password_hash,
    )

    mock_send_email.assert_called_once()


def register_user(
    client,
    email="login@example.com",
    password="Testing123!",
):
    otp = "123456"

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value=otp,
    ), patch(
        "app.api.v1.auth.send_verification_email",
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Test User",
                "email": email,
                "password": password,
            },
        )

    assert register_response.status_code == 202

    verify_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": email,
            "otp": otp,
        },
    )

    assert verify_response.status_code == 201

    return verify_response


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


def test_get_current_user(client):
    register_response = register_user(
        client,
        email="me@example.com",
    )

    registered_user = register_response.json()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "me@example.com",
            "password": "Testing123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registered_user["id"]
    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Test User"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid.jwt.token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_requires_authentication(client):
    response = client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code in (401, 403)


def test_update_current_user_display_name(client):
    register_user(
        client,
        email="profile@example.com",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "profile@example.com",
            "password": "Testing123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "display_name": "Updated Name",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["display_name"] == "Updated Name"
    assert data["email"] == "profile@example.com"


def test_update_current_user_trims_display_name(client):
    register_user(
        client,
        email="trim-profile@example.com",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "trim-profile@example.com",
            "password": "Testing123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "display_name": "   New Name   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "New Name"


def test_update_current_user_rejects_invalid_display_name(client):
    register_user(
        client,
        email="invalid-profile@example.com",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-profile@example.com",
            "password": "Testing123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "display_name": " ",
        },
    )

    assert response.status_code == 422


def test_update_current_user_requires_authentication(client):
    response = client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "Updated Name",
        },
    )

    assert response.status_code in (401, 403)

