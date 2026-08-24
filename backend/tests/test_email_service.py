from unittest.mock import Mock, patch

import httpx
import pytest

from app.core.config import settings
from app.services.email_service import (
    EmailDeliveryError,
    build_verification_email,
    send_verification_email,
)


def test_build_verification_email():
    message = build_verification_email(
        to_email="user@example.com",
        otp="123456",
    )

    assert (
        message["content"]["subject"]
        == "Your QuizApp verification code"
    )
    assert message["from"]["address"] == settings.twilio_from_email
    assert message["from"]["name"] == settings.twilio_from_name
    assert message["to"][0]["address"] == "user@example.com"

    html_content = message["content"]["html"]

    assert "123456" in html_content
    assert "Quiz" in html_content
    assert "App" in html_content
    assert (
        f"{settings.email_otp_expire_minutes} minutes"
        in html_content
    )


def test_send_verification_email_requires_credentials(monkeypatch):
    monkeypatch.setattr(settings, "twilio_api_key_sid", None)
    monkeypatch.setattr(settings, "twilio_api_key_secret", None)

    with pytest.raises(
        EmailDeliveryError,
        match="Twilio Email API credentials are not configured",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )


@patch("app.services.email_service.httpx.post")
def test_send_verification_email_success(
    mock_post,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "twilio_api_key_sid",
        "SK_test",
    )
    monkeypatch.setattr(
        settings,
        "twilio_api_key_secret",
        "test-secret",
    )

    response = Mock()
    response.status_code = 202
    mock_post.return_value = response

    send_verification_email(
        to_email="user@example.com",
        otp="123456",
    )

    mock_post.assert_called_once()

    _, kwargs = mock_post.call_args

    assert kwargs["auth"] == ("SK_test", "test-secret")
    assert kwargs["timeout"] == 10.0

    payload = kwargs["json"]

    assert payload["from"]["address"] == settings.twilio_from_email
    assert payload["from"]["name"] == settings.twilio_from_name
    assert payload["to"][0]["address"] == "user@example.com"
    assert (
        payload["content"]["subject"]
        == "Your QuizApp verification code"
    )
    assert "123456" in payload["content"]["html"]


@patch("app.services.email_service.httpx.post")
def test_send_verification_email_rejects_failed_response(
    mock_post,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "twilio_api_key_sid",
        "SK_test",
    )
    monkeypatch.setattr(
        settings,
        "twilio_api_key_secret",
        "test-secret",
    )

    response = Mock()
    response.status_code = 400
    mock_post.return_value = response

    with pytest.raises(
        EmailDeliveryError,
        match="Twilio Email rejected the verification email",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )


@patch("app.services.email_service.httpx.post")
def test_send_verification_email_handles_http_error(
    mock_post,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "twilio_api_key_sid",
        "SK_test",
    )
    monkeypatch.setattr(
        settings,
        "twilio_api_key_secret",
        "test-secret",
    )

    mock_post.side_effect = httpx.ConnectError(
        "network failure",
    )

    with pytest.raises(
        EmailDeliveryError,
        match="Failed to send verification email",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )