from unittest.mock import patch

from app.schemas.ai import (
    AnswerEvaluationResponse,
    CategorySuggestionResponse,
    IncorrectAnswerExplanationResponse,
    MathAnswerEvaluationResponse,
    TagSuggestionResponse,
)
from app.services.ai_service import (
    evaluate_math_answer,
    evaluate_written_answer,
    generate_incorrect_answer_explanation,
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


def test_evaluate_written_answer_accepts_semantically_correct_answer():
    parsed_result = AnswerEvaluationResponse(
        is_correct=True,
        explanation="Jupiter is the largest planet in the solar system.",
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = evaluate_written_answer(
            question_text=(
                "What is the largest planet in the solar system?"
            ),
            submitted_answer="jupiter",
        )

    assert result.is_correct is True
    assert result.explanation == (
        "Jupiter is the largest planet in the solar system."
    )
    mock_client.responses.parse.assert_called_once()


def test_evaluate_written_answer_returns_incorrect_with_explanation():
    parsed_result = AnswerEvaluationResponse(
        is_correct=False,
        explanation=(
            "Mars is not the largest planet. Jupiter is the "
            "largest planet in the solar system."
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = evaluate_written_answer(
            question_text=(
                "What is the largest planet in the solar system?"
            ),
            submitted_answer="Mars",
        )

    assert result.is_correct is False
    assert "Jupiter" in result.explanation
    mock_client.responses.parse.assert_called_once()


def test_generate_incorrect_answer_explanation():
    parsed_result = IncorrectAnswerExplanationResponse(
        explanation=(
            "Dividing both sides of 2x = 6 by 2 gives x = 3, "
            "not x = 2."
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = generate_incorrect_answer_explanation(
            question_text="Solve: 2x + 4 = 10",
            submitted_answer="x = 2",
            correct_answer="x = 3",
        )

    assert "x = 3" in result.explanation
    mock_client.responses.parse.assert_called_once()


def test_evaluate_written_answer_raises_when_ai_returns_no_result():
    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = None

        try:
            evaluate_written_answer(
                question_text="What is Python?",
                submitted_answer="A programming language.",
            )
        except RuntimeError as exc:
            assert str(exc) == (
                "OpenAI did not return an answer evaluation"
            )
        else:
            raise AssertionError("Expected RuntimeError")


def test_generate_explanation_raises_when_ai_returns_no_result():
    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = None

        try:
            generate_incorrect_answer_explanation(
                question_text="What is 2 + 2?",
                submitted_answer="5",
                correct_answer="4",
            )
        except RuntimeError as exc:
            assert str(exc) == (
                "OpenAI did not return an incorrect-answer explanation"
            )
        else:
            raise AssertionError("Expected RuntimeError")

def test_evaluate_math_answer_accepts_equivalent_answer():
    parsed_result = MathAnswerEvaluationResponse(
        is_correct=True,
        explanation="6 / 2 is equivalent to 3.",
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = evaluate_math_answer(
            question_text="Solve x = 6 / 2.",
            submitted_answer="3.0",
            expected_answer="3",
        )

    assert result.is_correct is True
    assert result.explanation == "6 / 2 is equivalent to 3."
    mock_client.responses.parse.assert_called_once()


def test_evaluate_math_answer_supports_non_math_semantic_answer():
    parsed_result = MathAnswerEvaluationResponse(
        is_correct=True,
        explanation=(
            "The submitted answer has the same meaning as the "
            "expected answer."
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = evaluate_math_answer(
            question_text="What is the star at the center of our solar system?",
            submitted_answer="sun",
            expected_answer="The Sun",
        )

    assert result.is_correct is True
    mock_client.responses.parse.assert_called_once()


def test_evaluate_math_answer_returns_incorrect_with_explanation():
    parsed_result = MathAnswerEvaluationResponse(
        is_correct=False,
        explanation=(
            "Subtracting 4 gives 2x = 6. Dividing both sides "
            "by 2 gives x = 3, not x = 2."
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = parsed_result

        result = evaluate_math_answer(
            question_text="Solve: 2x + 4 = 10",
            submitted_answer="x = 2",
            expected_answer="x = 3",
        )

    assert result.is_correct is False
    assert "x = 3" in result.explanation
    mock_client.responses.parse.assert_called_once()
