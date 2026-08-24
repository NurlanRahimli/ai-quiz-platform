from unittest.mock import Mock, patch

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

    assert message.subject.subject == "Your QuizApp verification code"

    payload = message.get()

    assert payload["from"]["email"] == settings.sendgrid_from_email
    assert payload["from"]["name"] == settings.sendgrid_from_name
    assert payload["personalizations"][0]["to"][0]["email"] == (
        "user@example.com"
    )

    html_content = payload["content"][0]["value"]

    assert "123456" in html_content
    assert "Quiz" in html_content
    assert "App" in html_content
    assert (
        f"{settings.email_otp_expire_minutes} minutes"
        in html_content
    )


def test_send_verification_email_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "sendgrid_api_key", None)

    with pytest.raises(
        EmailDeliveryError,
        match="SendGrid API key is not configured",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )


@patch("app.services.email_service.SendGridAPIClient")
def test_send_verification_email_success(
    mock_sendgrid_client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "sendgrid_api_key",
        "test-api-key",
    )

    response = Mock()
    response.status_code = 202

    client = Mock()
    client.send.return_value = response
    mock_sendgrid_client.return_value = client

    send_verification_email(
        to_email="user@example.com",
        otp="123456",
    )

    mock_sendgrid_client.assert_called_once_with("test-api-key")
    client.send.assert_called_once()


@patch("app.services.email_service.SendGridAPIClient")
def test_send_verification_email_rejects_failed_response(
    mock_sendgrid_client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "sendgrid_api_key",
        "test-api-key",
    )

    response = Mock()
    response.status_code = 400

    client = Mock()
    client.send.return_value = response
    mock_sendgrid_client.return_value = client

    with pytest.raises(
        EmailDeliveryError,
        match="SendGrid rejected the verification email",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )


@patch("app.services.email_service.SendGridAPIClient")
def test_send_verification_email_handles_sendgrid_exception(
    mock_sendgrid_client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "sendgrid_api_key",
        "test-api-key",
    )

    client = Mock()
    client.send.side_effect = RuntimeError("network failure")
    mock_sendgrid_client.return_value = client

    with pytest.raises(
        EmailDeliveryError,
        match="Failed to send verification email",
    ):
        send_verification_email(
            to_email="user@example.com",
            otp="123456",
        )