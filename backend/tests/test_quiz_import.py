import io

from unittest.mock import Mock, patch

from app.schemas.ai import ExtractedQuiz
from app.services.ai_service import (
    QuizImportQuestionLimitError,
    extract_quiz_from_file,
    validate_extracted_quiz,
)
import pytest
from fastapi import UploadFile
from tests.conftest import register_verified_user

from app.core.quiz_import import MAX_QUIZ_IMPORT_FILE_SIZE
from app.services.quiz_import_service import (
    QuizImportValidationError,
    validate_quiz_import_file,
)


@pytest.mark.anyio
async def test_accepts_pdf():
    file = UploadFile(
        filename="quiz.pdf",
        file=io.BytesIO(b"%PDF-1.7 test"),
        headers={"content-type": "application/pdf"},
    )

    contents = await validate_quiz_import_file(file)

    assert contents == b"%PDF-1.7 test"


def make_imported_question(
    number: int = 1,
    *,
    answer_source: str = "document",
    needs_review: bool = False,
):
    if answer_source == "unavailable":
        return {
            "question_type": "multiple_choice",
            "text": f"Question {number}",
            "choices": [
                {
                    "text": "Answer A",
                    "is_correct": False,
                },
                {
                    "text": "Answer B",
                    "is_correct": False,
                },
            ],
            "answer_source": "unavailable",
            "needs_review": True,
            "review_reason": "The correct answer could not be determined.",
        }

    return {
        "question_type": "multiple_choice",
        "text": f"Question {number}",
        "choices": [
            {
                "text": "Answer A",
                "is_correct": True,
            },
            {
                "text": "Answer B",
                "is_correct": False,
            },
        ],
        "answer_source": answer_source,
        "needs_review": needs_review,
    }


def register_and_login(client):
    email = "quiz-import@example.com"
    password = "Password123!"

    register_verified_user(
        client,
        email=email,
        display_name="Quiz Import User",
        password=password,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


@pytest.mark.anyio
async def test_accepts_jpg():
    file = UploadFile(
        filename="quiz.jpg",
        file=io.BytesIO(b"\xff\xd8\xff test"),
        headers={"content-type": "image/jpeg"},
    )

    contents = await validate_quiz_import_file(file)

    assert contents == b"\xff\xd8\xff test"


@pytest.mark.anyio
async def test_accepts_jpeg():
    file = UploadFile(
        filename="quiz.jpeg",
        file=io.BytesIO(b"\xff\xd8\xff test"),
        headers={"content-type": "image/jpeg"},
    )

    contents = await validate_quiz_import_file(file)

    assert contents == b"\xff\xd8\xff test"


@pytest.mark.anyio
async def test_accepts_png():
    contents = b"\x89PNG\r\n\x1a\n test"

    file = UploadFile(
        filename="quiz.png",
        file=io.BytesIO(contents),
        headers={"content-type": "image/png"},
    )

    result = await validate_quiz_import_file(file)

    assert result == contents


@pytest.mark.anyio
async def test_rejects_unsupported_extension():
    file = UploadFile(
        filename="quiz.txt",
        file=io.BytesIO(b"quiz"),
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="Please upload a PDF, JPG, JPEG, or PNG file.",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_invalid_content_type():
    file = UploadFile(
        filename="quiz.pdf",
        file=io.BytesIO(b"%PDF-1.7 test"),
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="Please upload a valid PDF, JPG, JPEG, or PNG file.",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_empty_file():
    file = UploadFile(
        filename="quiz.pdf",
        file=io.BytesIO(b""),
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="The uploaded file is empty.",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_oversized_file():
    file = UploadFile(
        filename="quiz.pdf",
        file=io.BytesIO(
            b"x" * (MAX_QUIZ_IMPORT_FILE_SIZE + 1)
        ),
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="The uploaded file must be 10 MB or smaller.",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_fake_pdf():
    file = UploadFile(
        filename="quiz.pdf",
        file=io.BytesIO(b"This is not actually a PDF"),
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="does not appear to be a valid",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_fake_jpeg():
    file = UploadFile(
        filename="quiz.jpg",
        file=io.BytesIO(b"This is not actually a JPEG"),
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="does not appear to be a valid",
    ):
        await validate_quiz_import_file(file)


@pytest.mark.anyio
async def test_rejects_fake_png():
    file = UploadFile(
        filename="quiz.png",
        file=io.BytesIO(b"This is not actually a PNG"),
        headers={"content-type": "image/png"},
    )

    with pytest.raises(
        QuizImportValidationError,
        match="does not appear to be a valid",
    ):
        await validate_quiz_import_file(file)


def test_import_quiz_requires_authentication(client):
    response = client.post(
        "/api/v1/ai/import-quiz",
        files={
            "file": (
                "quiz.pdf",
                b"%PDF-1.7 test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 401


@patch("app.api.v1.ai.extract_quiz_from_file")
def test_import_quiz_accepts_pdf(
    mock_extract_quiz,
    client,
):
    headers = register_and_login(client)

    mock_extract_quiz.return_value = {
        "title": "Python Fundamentals",
        "description": "A quiz about Python basics.",
        "category": "Programming",
        "tags": ["Python", "Fundamentals"],
        "questions": [
            make_imported_question(
                answer_source="document",
            )
        ],
    }

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.pdf",
                b"%PDF-1.7 test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Python Fundamentals"
    assert data["category"] == "Programming"
    assert data["tags"] == ["Python", "Fundamentals"]
    assert len(data["questions"]) == 1
    assert data["questions"][0]["answer_source"] == "document"

    mock_extract_quiz.assert_called_once_with(
        contents=b"%PDF-1.7 test",
        content_type="application/pdf",
    )


@patch("app.api.v1.ai.extract_quiz_from_file")
def test_import_quiz_accepts_jpeg(
    mock_extract_quiz,
    client,
):
    headers = register_and_login(client)

    mock_extract_quiz.return_value = {
        "title": None,
        "description": None,
        "category": "Science",
        "tags": ["Biology"],
        "questions": [
            make_imported_question(
                answer_source="ai_inferred",
            )
        ],
    }

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.jpg",
                b"\xff\xd8\xff test",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] is None
    assert data["category"] == "Science"
    assert data["questions"][0]["answer_source"] == "ai_inferred"

    mock_extract_quiz.assert_called_once_with(
        contents=b"\xff\xd8\xff test",
        content_type="image/jpeg",
    )


@patch("app.api.v1.ai.extract_quiz_from_file")
def test_import_quiz_accepts_png(
    mock_extract_quiz,
    client,
):
    headers = register_and_login(client)

    mock_extract_quiz.return_value = {
        "title": "Geography Quiz",
        "description": None,
        "category": "Geography",
        "tags": ["Countries"],
        "questions": [
            make_imported_question(
                answer_source="unavailable",
            )
        ],
    }

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.png",
                b"\x89PNG\r\n\x1a\n test",
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category"] == "Geography"
    assert data["questions"][0]["answer_source"] == "unavailable"
    assert data["questions"][0]["needs_review"] is True

    mock_extract_quiz.assert_called_once_with(
        contents=b"\x89PNG\r\n\x1a\n test",
        content_type="image/png",
    )


@patch("app.api.v1.ai.extract_quiz_from_file")
def test_import_quiz_rejects_more_than_30_questions(
    mock_extract_quiz,
    client,
):
    headers = register_and_login(client)

    mock_extract_quiz.side_effect = QuizImportQuestionLimitError(
        "This quiz contains more than 30 questions. "
        "Keep only 30 questions and try again."
    )

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.pdf",
                b"%PDF-1.7 test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "This quiz contains more than 30 questions. "
        "Keep only 30 questions and try again."
    )


@patch("app.api.v1.ai.extract_quiz_from_file")
def test_import_quiz_handles_ai_failure(
    mock_extract_quiz,
    client,
):
    headers = register_and_login(client)

    mock_extract_quiz.side_effect = RuntimeError(
        "OpenAI extraction failed"
    )

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.pdf",
                b"%PDF-1.7 test",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unable to import the quiz right now."
    )


def test_import_quiz_rejects_unsupported_file(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.txt",
                b"not a quiz document",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Please upload a PDF, JPG, JPEG, or PNG file."
    )


def test_import_quiz_rejects_fake_pdf(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/ai/import-quiz",
        headers=headers,
        files={
            "file": (
                "quiz.pdf",
                b"this is not actually a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The uploaded file does not appear to be a valid "
        "PDF, JPG, JPEG, or PNG file."
    )


def test_validate_extracted_quiz_accepts_30_questions():
    extracted = ExtractedQuiz(
        title="Thirty Question Quiz",
        category="General Knowledge",
        tags=["Test"],
        questions=[
            make_imported_question(number)
            for number in range(1, 31)
        ],
    )

    result = validate_extracted_quiz(extracted)

    assert len(result.questions) == 30


def test_validate_extracted_quiz_rejects_more_than_30_questions():
    extracted = ExtractedQuiz(
        title="Large Quiz",
        category="General Knowledge",
        tags=["Test"],
        questions=[
            make_imported_question(number)
            for number in range(1, 32)
        ],
    )

    with pytest.raises(
        QuizImportQuestionLimitError,
        match=(
            "This quiz contains more than 30 questions. "
            "Keep only 30 questions and try again."
        ),
    ):
        validate_extracted_quiz(extracted)


def test_validate_extracted_quiz_preserves_ai_inferred_answer():
    extracted = ExtractedQuiz(
        title="Science Quiz",
        category="Science",
        tags=["Science"],
        questions=[
            make_imported_question(
                answer_source="ai_inferred",
            )
        ],
    )

    result = validate_extracted_quiz(extracted)

    question = result.questions[0]

    assert question.answer_source == "ai_inferred"
    assert question.needs_review is False
    assert sum(
        choice.is_correct
        for choice in question.choices
    ) == 1


def test_validate_extracted_quiz_preserves_uncertain_answer():
    extracted = ExtractedQuiz(
        title="Review Quiz",
        category="General Knowledge",
        tags=[],
        questions=[
            make_imported_question(
                answer_source="unavailable",
            )
        ],
    )

    result = validate_extracted_quiz(extracted)

    question = result.questions[0]

    assert question.answer_source == "unavailable"
    assert question.needs_review is True
    assert question.review_reason is not None
    assert not any(
        choice.is_correct
        for choice in question.choices
    )


@patch("app.services.ai_service.OpenAI")
def test_extract_quiz_from_pdf(mock_openai, monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_service.settings.openai_api_key",
        "test-api-key",
    )

    extracted = ExtractedQuiz(
        title="Python Quiz",
        description="Python fundamentals.",
        category="Programming",
        tags=["Python", "Fundamentals"],
        questions=[
            make_imported_question(
                answer_source="document",
            )
        ],
    )

    response = Mock()
    response.output_parsed = extracted

    client = Mock()
    client.responses.parse.return_value = response
    mock_openai.return_value = client

    result = extract_quiz_from_file(
        contents=b"%PDF-1.7 test",
        content_type="application/pdf",
    )

    assert result.title == "Python Quiz"
    assert result.category == "Programming"
    assert len(result.questions) == 1

    mock_openai.assert_called_once_with(
        api_key="test-api-key",
    )
    client.responses.parse.assert_called_once()


@patch("app.services.ai_service.OpenAI")
def test_extract_quiz_from_image(mock_openai, monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_service.settings.openai_api_key",
        "test-api-key",
    )

    extracted = ExtractedQuiz(
        title=None,
        description=None,
        category="Science",
        tags=["Biology"],
        questions=[
            make_imported_question(
                answer_source="ai_inferred",
            )
        ],
    )

    response = Mock()
    response.output_parsed = extracted

    client = Mock()
    client.responses.parse.return_value = response
    mock_openai.return_value = client

    result = extract_quiz_from_file(
        contents=b"\xff\xd8\xff test",
        content_type="image/jpeg",
    )

    assert result.title is None
    assert result.category == "Science"
    assert result.questions[0].answer_source == "ai_inferred"

    client.responses.parse.assert_called_once()