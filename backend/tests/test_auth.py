import uuid
from sqlalchemy import select
from tests.conftest import register_verified_user
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.services.email_service import EmailDeliveryError
from app.core.security import hash_otp, hash_password

from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset

from app.models.user import User
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
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
    display_name="Test User",
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
                "display_name": display_name,
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

def test_register_rejects_taken_display_name_case_insensitively(
    client,
):
    register_user(
        client,
        email="display-name-existing@example.com",
        display_name="Unique Registration Name",
    )

    with patch(
        "app.api.v1.auth.send_verification_email",
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "unique registration name",
                "email": "display-name-new@example.com",
                "password": "Testing123!",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Display name is already taken"
    )


def test_verify_email_rechecks_display_name_uniqueness(
    client,
):
    otp = "123456"

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value=otp,
    ), patch(
        "app.api.v1.auth.send_verification_email",
    ):
        pending_response = client.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Pending Unique Name",
                "email": "pending-name@example.com",
                "password": "Testing123!",
            },
        )

    assert pending_response.status_code == 202

    register_user(
        client,
        email="claimed-name@example.com",
        display_name="Pending Unique Name",
    )

    response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": "pending-name@example.com",
            "otp": otp,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Display name is already taken"
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



def test_update_current_user_rejects_taken_display_name_case_insensitively(
    client,
):
    register_user(
        client,
        email="display-name-owner@example.com",
        display_name="Unique Display Name",
    )

    register_user(
        client,
        email="display-name-other@example.com",
        display_name="Other Display Name",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "display-name-other@example.com",
            "password": "Testing123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "display_name": "unique display name",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Display name is already taken"
    )

def test_update_current_user_can_keep_own_display_name(
    client,
):
    register_user(
        client,
        email="keep-display-name@example.com",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "keep-display-name@example.com",
            "password": "Testing123!",
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }

    first_response = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "display_name": "Keep My Name",
        },
    )

    assert first_response.status_code == 200

    second_response = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "display_name": "keep my name",
        },
    )

    assert second_response.status_code == 200
    assert (
        second_response.json()["display_name"]
        == "keep my name"
    )


def test_change_password_successfully_updates_password(client):
    email = "change-password@example.com"
    old_password = "Testing123!"
    new_password = "ChangedPassword123!"

    register_user(
        client,
        email=email,
        password=old_password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": old_password,
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me/password",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": old_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 204
    assert response.content == b""

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": old_password,
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": new_password,
        },
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


def test_change_password_rejects_incorrect_current_password(client):
    email = "wrong-current-password@example.com"

    register_user(
        client,
        email=email,
        password="Testing123!",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Testing123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me/password",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": "WrongPassword123!",
            "new_password": "ChangedPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"

    original_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Testing123!",
        },
    )
    assert original_login.status_code == 200


def test_change_password_rejects_same_password(client):
    email = "same-password@example.com"
    password = "Testing123!"

    register_user(
        client,
        email=email,
        password=password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me/password",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": password,
            "new_password": password,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "New password must be different from current password"
    )


def test_change_password_rejects_short_new_password(client):
    email = "short-new-password@example.com"

    register_user(
        client,
        email=email,
        password="Testing123!",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Testing123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me/password",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": "Testing123!",
            "new_password": "short",
        },
    )

    assert response.status_code == 422


def test_change_password_requires_authentication(client):
    response = client.patch(
        "/api/v1/auth/me/password",
        json={
            "current_password": "Testing123!",
            "new_password": "ChangedPassword123!",
        },
    )

    assert response.status_code == 401


def test_delete_account_rejects_incorrect_password(
    client,
    db,
):
    email = "delete-wrong-password@example.com"
    password = "Testing123!"

    register_verified_user(
        client,
        email=email,
        display_name="Delete Wrong Password",
        password=password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }

    response = client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers=headers,
        json={
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password is incorrect"

    user = db.scalar(
        select(User).where(User.email == email)
    )

    assert user is not None


def test_delete_account_removes_current_user(
    client,
    db,
):
    email = "delete-account@example.com"
    password = "Testing123!"

    register_verified_user(
        client,
        email=email,
        display_name="Delete Account User",
        password=password,
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }

    response = client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers=headers,
        json={
            "password": password,
        },
    )

    assert response.status_code == 204

    db.expire_all()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    assert user is None


def test_delete_account_requires_authentication(client):
    response = client.request(
        "DELETE",
        "/api/v1/auth/me",
        json={
            "password": "Testing123!",
        },
    )

    assert response.status_code in {401, 403}


def test_delete_account_cascades_all_user_data(
    client,
    db,
):
    password = "Testing123!"

    # -----------------------------------------------------
    # User A: account that will be deleted
    # -----------------------------------------------------

    user_a = register_verified_user(
        client,
        email="delete-cascade-a@example.com",
        display_name="Delete Cascade A",
        password=password,
    )

    login_a = client.post(
        "/api/v1/auth/login",
        json={
            "email": "delete-cascade-a@example.com",
            "password": password,
        },
    )

    assert login_a.status_code == 200

    headers_a = {
        "Authorization": (
            f"Bearer {login_a.json()['access_token']}"
        ),
    }

    # -----------------------------------------------------
    # User B: must survive User A deletion
    # -----------------------------------------------------

    user_b = register_verified_user(
        client,
        email="delete-cascade-b@example.com",
        display_name="Delete Cascade B",
        password=password,
    )

    user_a_id = uuid.UUID(user_a["id"])
    user_b_id = uuid.UUID(user_b["id"])

    login_b = client.post(
        "/api/v1/auth/login",
        json={
            "email": "delete-cascade-b@example.com",
            "password": password,
        },
    )

    assert login_b.status_code == 200

    headers_b = {
        "Authorization": (
            f"Bearer {login_b.json()['access_token']}"
        ),
    }

    # -----------------------------------------------------
    # User A creates their own quiz.
    # It should disappear when User A is deleted.
    # -----------------------------------------------------

    owned_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers_a,
        json={
            "title": "User A Owned Quiz",
            "description": "Must be deleted with User A",
        },
    )

    assert owned_quiz_response.status_code == 201

    owned_quiz_id = uuid.UUID(owned_quiz_response.json()["id"])

    # -----------------------------------------------------
    # User B creates a quiz.
    # It must survive User A deletion.
    # -----------------------------------------------------

    surviving_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers_b,
        json={
            "title": "User B Surviving Quiz",
            "description": "Must survive User A deletion",
        },
    )

    assert surviving_quiz_response.status_code == 201

    surviving_quiz_id = uuid.UUID(surviving_quiz_response.json()["id"])

    question_response = client.post(
        (
            f"/api/v1/quizzes/"
            f"{surviving_quiz_id}/questions"
        ),
        headers=headers_b,
        json={
            "text": "What is 2 + 2?",
            "choices": [
                {
                    "text": "3",
                    "is_correct": False,
                },
                {
                    "text": "4",
                    "is_correct": True,
                },
            ],
        },
    )

    assert question_response.status_code == 201

    question = question_response.json()

    correct_choice = next(
        choice
        for choice in question["answer_choices"]
        if choice["is_correct"]
    )

    # -----------------------------------------------------
    # User A attempts User B's quiz.
    # This attempt must disappear when User A is deleted.
    # -----------------------------------------------------

    attempt_response = client.post(
        (
            f"/api/v1/quizzes/"
            f"{surviving_quiz_id}/attempts"
        ),
        headers=headers_a,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_choice_id": correct_choice["id"],
                },
            ],
        },
    )

    assert attempt_response.status_code == 201

    attempt_id = uuid.UUID(attempt_response.json()["id"])

    # Confirm test data exists before deletion.
    assert db.get(User, user_a_id) is not None
    assert db.get(User, user_b_id) is not None

    assert db.get(Quiz, owned_quiz_id) is not None
    assert db.get(Quiz, surviving_quiz_id) is not None

    assert db.get(QuizAttempt, attempt_id) is not None

    attempt_answers_before = db.scalars(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt_id
        )
    ).all()

    assert len(attempt_answers_before) == 1

    # -----------------------------------------------------
    # Delete User A
    # -----------------------------------------------------

    delete_response = client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers=headers_a,
        json={
            "password": password,
        },
    )

    assert delete_response.status_code == 204

    # The API request uses a separate database session.
    # End this fixture session's current transaction so the
    # following reads see the committed cascade deletion.
    db.rollback()
    db.expire_all()

    # -----------------------------------------------------
    # User A and User A-owned data must be gone.
    # -----------------------------------------------------

    assert db.get(User, user_a_id) is None
    assert db.get(Quiz, owned_quiz_id) is None

    # User A's attempt on somebody else's quiz must be gone.
    assert db.get(QuizAttempt, attempt_id) is None

    attempt_answers_after = db.scalars(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt_id
        )
    ).all()

    assert attempt_answers_after == []

    # -----------------------------------------------------
    # User B and User B's quiz must remain untouched.
    # -----------------------------------------------------

    assert db.get(User, user_b_id) is not None
    assert db.get(Quiz, surviving_quiz_id) is not None

    surviving_quiz_response = client.get(
        f"/api/v1/quizzes/{surviving_quiz_id}",
        headers=headers_b,
    )

    assert surviving_quiz_response.status_code == 200



@patch("app.api.v1.auth.send_password_reset_email")
def test_forgot_password_creates_reset_for_existing_user(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="forgot-existing@example.com",
        password="Testing123!",
        display_name="Forgot Existing",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={
                "email": "forgot-existing@example.com",
            },
        )

    assert response.status_code == 202
    assert response.json() == {
        "message": (
            "If an account exists for this email, "
            "a password reset code has been sent."
        )
    }

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "forgot-existing@example.com"
        )
    )

    assert password_reset is not None
    assert password_reset.otp_hash
    assert password_reset.attempt_count == 0
    assert password_reset.expires_at is not None
    assert password_reset.last_sent_at is not None

    mock_send_email.assert_called_once_with(
        to_email="forgot-existing@example.com",
        otp="123456",
    )


@patch("app.api.v1.auth.send_password_reset_email")
def test_forgot_password_does_not_reveal_unknown_email(
    mock_send_email,
    client,
    db,
):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "does-not-exist@example.com",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "message": (
            "If an account exists for this email, "
            "a password reset code has been sent."
        )
    }

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "does-not-exist@example.com"
        )
    )

    assert password_reset is None
    mock_send_email.assert_not_called()


@patch("app.api.v1.auth.send_password_reset_email")
def test_forgot_password_normalizes_email(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="forgot-normalized@example.com",
        password="Testing123!",
        display_name="Forgot Normalized",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={
                "email": "FORGOT-NORMALIZED@EXAMPLE.COM",
            },
        )

    assert response.status_code == 202

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "forgot-normalized@example.com"
        )
    )

    assert password_reset is not None

    mock_send_email.assert_called_once_with(
        to_email="forgot-normalized@example.com",
        otp="123456",
    )


@patch("app.api.v1.auth.send_password_reset_email")
def test_forgot_password_enforces_resend_cooldown(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="forgot-cooldown@example.com",
        password="Testing123!",
        display_name="Forgot Cooldown",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        first_response = client.post(
            "/api/v1/auth/forgot-password",
            json={
                "email": "forgot-cooldown@example.com",
            },
        )

    assert first_response.status_code == 202

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "forgot-cooldown@example.com"
        )
    )

    assert password_reset is not None

    original_otp_hash = password_reset.otp_hash
    original_expires_at = password_reset.expires_at

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="654321",
    ):
        second_response = client.post(
            "/api/v1/auth/forgot-password",
            json={
                "email": "forgot-cooldown@example.com",
            },
        )

    assert second_response.status_code == 202
    assert second_response.json() == first_response.json()

    db.refresh(password_reset)

    assert password_reset.otp_hash == original_otp_hash
    assert password_reset.expires_at == original_expires_at

    assert mock_send_email.call_count == 1


@patch(
    "app.api.v1.auth.send_password_reset_email",
    side_effect=EmailDeliveryError("Twilio failed"),
)
def test_forgot_password_does_not_persist_when_email_delivery_fails(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="forgot-delivery-failure@example.com",
        password="Testing123!",
        display_name="Forgot Delivery Failure",
    )

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "forgot-delivery-failure@example.com",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unable to send password reset email"
    )

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email
            == "forgot-delivery-failure@example.com"
        )
    )

    assert password_reset is None
    mock_send_email.assert_called_once()


@patch("app.api.v1.auth.send_password_reset_email")
def test_verify_password_reset_returns_reset_token_for_valid_otp(
    mock_send_email,
    client,
):
    register_verified_user(
        client,
        email="reset-verify@example.com",
        password="Testing123!",
        display_name="Reset Verify",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset-verify@example.com"},
        )

    assert forgot_response.status_code == 202

    response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": "reset-verify@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["reset_token"]
    assert body["token_type"] == "bearer"

    payload = jwt.decode(
        body["reset_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "reset-verify@example.com"
    assert payload["purpose"] == "password_reset"
    assert payload["exp"]


@patch("app.api.v1.auth.send_password_reset_email")
def test_verify_password_reset_rejects_invalid_otp_and_increments_attempts(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="reset-wrong@example.com",
        password="Testing123!",
        display_name="Reset Wrong",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset-wrong@example.com"},
        )

    response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": "reset-wrong@example.com",
            "otp": "654321",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification code"

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "reset-wrong@example.com"
        )
    )

    assert password_reset is not None
    assert password_reset.attempt_count == 1


@patch("app.api.v1.auth.send_password_reset_email")
def test_verify_password_reset_rejects_expired_otp(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="reset-expired@example.com",
        password="Testing123!",
        display_name="Reset Expired",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset-expired@example.com"},
        )

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "reset-expired@example.com"
        )
    )

    assert password_reset is not None

    password_reset.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": "reset-expired@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset code"
    )


@patch("app.api.v1.auth.send_password_reset_email")
def test_verify_password_reset_blocks_after_max_attempts(
    mock_send_email,
    client,
    db,
):
    register_verified_user(
        client,
        email="reset-attempts@example.com",
        password="Testing123!",
        display_name="Reset Attempts",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset-attempts@example.com"},
        )

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == "reset-attempts@example.com"
        )
    )

    assert password_reset is not None

    password_reset.attempt_count = settings.email_otp_max_attempts
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": "reset-attempts@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "Too many verification attempts"
    )


def test_verify_password_reset_rejects_missing_reset_request(
    client,
):
    response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": "no-reset@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset code"
    )


@patch("app.api.v1.auth.send_password_reset_email")
def test_reset_password_full_flow(
    mock_send_email,
    client,
    db,
):
    email = "full-reset@example.com"
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    register_verified_user(
        client,
        email=email,
        password=old_password,
        display_name="Full Reset",
    )

    # Old password works before reset.
    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": old_password,
        },
    )
    assert old_login.status_code == 200

    # Request reset OTP.
    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

    assert forgot_response.status_code == 202

    # Verify OTP and receive short-lived reset token.
    verify_response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200

    reset_token = verify_response.json()["reset_token"]

    # Change password.
    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
        },
    )

    assert reset_response.status_code == 200
    assert reset_response.json() == {
        "message": "Password reset successfully"
    }

    # Reset request is consumed.
    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == email
        )
    )
    assert password_reset is None

    # Old password no longer works.
    old_login_after_reset = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": old_password,
        },
    )

    assert old_login_after_reset.status_code == 401

    # New password works.
    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": new_password,
        },
    )

    assert new_login.status_code == 200
    assert new_login.json()["access_token"]

    # Same reset token cannot be reused.
    reuse_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "AnotherPassword789!",
        },
    )

    assert reuse_response.status_code == 400
    assert reuse_response.json()["detail"] == (
        "Invalid or expired password reset token"
    )


def test_reset_password_rejects_invalid_token(
    client,
):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": "not-a-valid-token",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token"
    )


def test_reset_password_rejects_normal_access_token(
    client,
):
    email = "normal-token@example.com"
    password = "Testing123!"

    register_verified_user(
        client,
        email=email,
        password=password,
        display_name="Normal Token",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": access_token,
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token"
    )


@patch("app.api.v1.auth.send_password_reset_email")
def test_reset_password_rejects_expired_reset_record(
    mock_send_email,
    client,
    db,
):
    email = "expired-final-reset@example.com"

    register_verified_user(
        client,
        email=email,
        password="Testing123!",
        display_name="Expired Final Reset",
    )

    with patch(
        "app.api.v1.auth.generate_otp",
        return_value="123456",
    ):
        client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

    verify_response = client.post(
        "/api/v1/auth/verify-password-reset",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert verify_response.status_code == 200
    reset_token = verify_response.json()["reset_token"]

    password_reset = db.scalar(
        select(PasswordReset).where(
            PasswordReset.email == email
        )
    )

    assert password_reset is not None

    password_reset.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    db.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token"
    )
