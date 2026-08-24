from unittest.mock import patch

from app.schemas.ai import (
    CategorySuggestionResponse,
    TagSuggestionResponse,
)
from tests.conftest import register_verified_user


def register_and_login(
    client,
    *,
    email: str = "ai-user@example.com",
    display_name: str = "AI User",
    password: str = "Password123!",
):
    register_verified_user(
        client,
        email=email,
        display_name=display_name,
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

    return {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }


def quiz_context():
    return {
        "title": "Python Fundamentals",
        "description": "A quiz about basic Python programming.",
        "questions": [
            "What keyword defines a function in Python?",
            "What is a Python list?",
            "What does a for loop do?",
        ],
    }


def test_suggest_category_requires_authentication(client):
    response = client.post(
        "/api/v1/ai/suggest-category",
        json=quiz_context(),
    )

    assert response.status_code == 401


@patch("app.api.v1.ai.suggest_quiz_category")
def test_suggest_category_returns_ai_suggestion(
    mock_suggest_category,
    client,
):
    headers = register_and_login(client)

    mock_suggest_category.return_value = CategorySuggestionResponse(
        category="Programming"
    )

    response = client.post(
        "/api/v1/ai/suggest-category",
        headers=headers,
        json=quiz_context(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "category": "Programming",
    }

    mock_suggest_category.assert_called_once()


def test_suggest_category_requires_questions(client):
    headers = register_and_login(
        client,
        email="ai-validation@example.com",
        display_name="AI Validation",
    )

    payload = quiz_context()
    payload["questions"] = []

    response = client.post(
        "/api/v1/ai/suggest-category",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422


@patch("app.api.v1.ai.suggest_quiz_category")
def test_suggest_category_handles_ai_failure(
    mock_suggest_category,
    client,
):
    headers = register_and_login(
        client,
        email="ai-failure@example.com",
        display_name="AI Failure",
    )

    mock_suggest_category.side_effect = RuntimeError(
        "OpenAI request failed"
    )

    response = client.post(
        "/api/v1/ai/suggest-category",
        headers=headers,
        json=quiz_context(),
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Unable to generate a category suggestion right now."
    }


@patch("app.api.v1.ai.suggest_quiz_tags")
def test_suggest_tags_returns_ai_suggestions(
    mock_suggest_tags,
    client,
):
    headers = register_and_login(
        client,
        email="ai-tags@example.com",
        display_name="AI Tags",
    )

    mock_suggest_tags.return_value = TagSuggestionResponse(
        tags=[
            "Python functions",
            "Lists vs tuples",
            "For loops",
        ]
    )

    response = client.post(
        "/api/v1/ai/suggest-tags",
        headers=headers,
        json=quiz_context(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "tags": [
            "Python functions",
            "Lists vs tuples",
            "For loops",
        ]
    }

    mock_suggest_tags.assert_called_once()


def test_suggest_tags_requires_authentication(client):
    response = client.post(
        "/api/v1/ai/suggest-tags",
        json=quiz_context(),
    )

    assert response.status_code == 401


def test_suggest_tags_requires_questions(client):
    headers = register_and_login(
        client,
        email="ai-tags-validation@example.com",
        display_name="AI Tags Validation",
    )

    payload = quiz_context()
    payload["questions"] = []

    response = client.post(
        "/api/v1/ai/suggest-tags",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422


@patch("app.api.v1.ai.suggest_quiz_tags")
def test_suggest_tags_handles_ai_failure(
    mock_suggest_tags,
    client,
):
    headers = register_and_login(
        client,
        email="ai-tags-failure@example.com",
        display_name="AI Tags Failure",
    )

    mock_suggest_tags.side_effect = RuntimeError(
        "OpenAI request failed"
    )

    response = client.post(
        "/api/v1/ai/suggest-tags",
        headers=headers,
        json=quiz_context(),
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Unable to generate tag suggestions right now."
    }