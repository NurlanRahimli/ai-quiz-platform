import uuid

from unittest.mock import patch

from sqlalchemy import func, select

from app.models.audit_log import AuditLog
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.schemas.ai import (
    AnswerEvaluationResponse,
    IncorrectAnswerExplanationResponse,
    MathAnswerEvaluationResponse,
)
from tests.conftest import register_verified_user


def register_and_login(
    client,
    email="attempt-user@example.com",
    password="Password123!",
):
    display_name = f"Attempt {email.split('@', 1)[0]}"

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
        ),
    }


def create_quiz_with_questions(client, headers):
    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Quiz Attempt Test",
            "description": "Testing quiz submissions",
        },
    )
    assert quiz_response.status_code == 201

    quiz_id = quiz_response.json()["id"]

    multiple_choice_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
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
    assert multiple_choice_response.status_code == 201

    written_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/written",
        headers=headers,
        json={
            "text": "Explain what a variable is.",
        },
    )
    assert written_response.status_code == 201

    math_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/math-work",
        headers=headers,
        json={
            "text": "Solve 2x = 10 and show your work.",
            "expected_answer": "5",
        },
    )
    assert math_response.status_code == 201

    return {
        "quiz_id": quiz_id,
        "multiple_choice": multiple_choice_response.json(),
        "written": written_response.json(),
        "math": math_response.json(),
    }


def test_submit_quiz_attempt(client):
    headers = register_and_login(client)
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "2x = 10, so x = 5.",
                },
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["quiz_id"] == quiz["quiz_id"]
    assert len(data["answers"]) == 3
    assert data["submitted_at"] is not None


def test_attempt_requires_every_question(client):
    headers = register_and_login(
        client,
        email="missing-answer@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_attempt_rejects_duplicate_questions(client):
    headers = register_and_login(
        client,
        email="duplicate-answer@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "First answer",
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "Second answer",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_attempt_rejects_choice_from_another_question(client):
    headers = register_and_login(
        client,
        email="wrong-choice@example.com",
    )

    quiz = create_quiz_with_questions(client, headers)

    second_question_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/questions",
        headers=headers,
        json={
            "text": "What is 3 + 3?",
            "choices": [
                {
                    "text": "5",
                    "is_correct": False,
                },
                {
                    "text": "6",
                    "is_correct": True,
                },
            ],
        },
    )

    assert second_question_response.status_code == 201

    foreign_choice_id = (
        second_question_response.json()["answer_choices"][0]["id"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": foreign_choice_id,
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores data.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "x = 5",
                },
                {
                    "question_id": second_question_response.json()["id"],
                    "selected_choice_id": foreign_choice_id,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_attempt_rejects_empty_written_answer(client):
    headers = register_and_login(
        client,
        email="empty-written@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    choice_id = quiz["multiple_choice"]["answer_choices"][0]["id"]

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": choice_id,
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "   ",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "x = 5",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_submit_attempt_requires_authentication(client):
    response = client.post(
        "/api/v1/quizzes/00000000-0000-0000-0000-000000000000/attempts",
        json={
            "answers": [],
        },
    )

    assert response.status_code == 401


def test_get_quiz_attempt_results(client):
    headers = register_and_login(client)
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert submit_response.status_code == 201
    attempt_id = submit_response.json()["id"]

    response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results"
        ),
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["attempt_id"] == attempt_id
    assert data["quiz_id"] == quiz["quiz_id"]
    assert data["score"] == 3
    assert data["gradable_questions"] == 3
    assert data["total_questions"] == 3

    results = {
        answer["question_type"]: answer
        for answer in data["answers"]
    }

    assert results["multiple_choice"]["is_correct"] is True
    assert results["multiple_choice"]["submitted_answer"] == "4"
    assert results["multiple_choice"]["correct_answer"] == "4"

    multiple_choice_options = results["multiple_choice"]["answer_choices"]

    assert len(multiple_choice_options) == len(
        quiz["multiple_choice"]["answer_choices"]
    )

    selected_options = [
        choice
        for choice in multiple_choice_options
        if choice["was_selected"]
    ]

    assert len(selected_options) == 1
    assert selected_options[0]["id"] == correct_choice["id"]
    assert selected_options[0]["is_correct"] is True

    assert multiple_choice_options == sorted(
        multiple_choice_options,
        key=lambda choice: choice["position"],
    )

    assert results["math_work"]["answer_choices"] == []
    assert results["written_answer"]["answer_choices"] == []

    assert results["math_work"]["is_correct"] is True
    assert results["math_work"]["submitted_answer"] == "5"
    assert results["math_work"]["correct_answer"] == "5"

    assert results["written_answer"]["is_correct"] is True
    assert results["written_answer"]["correct_answer"] is None


def test_results_show_incorrect_answers(client):
    headers = register_and_login(client)
    quiz = create_quiz_with_questions(client, headers)

    incorrect_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if not choice["is_correct"]
    )

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": incorrect_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "My written response.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "7",
                },
            ],
        },
    )

    assert submit_response.status_code == 201
    attempt_id = submit_response.json()["id"]

    response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results"
        ),
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    results = {
        answer["question_type"]: answer
        for answer in data["answers"]
    }

    multiple_choice_options = results["multiple_choice"]["answer_choices"]

    selected_option = next(
        choice
        for choice in multiple_choice_options
        if choice["was_selected"]
    )

    correct_option = next(
        choice
        for choice in multiple_choice_options
        if choice["is_correct"]
    )

    assert selected_option["id"] == incorrect_choice["id"]
    assert selected_option["is_correct"] is False
    assert correct_option["is_correct"] is True
    assert correct_option["was_selected"] is False

    assert data["score"] == 0
    assert data["gradable_questions"] == 3
    assert data["total_questions"] == 3

    graded_answers = [
        answer
        for answer in data["answers"]
        if answer["is_correct"] is not None
    ]

    assert len(graded_answers) == 3
    assert all(
        answer["is_correct"] is False
        for answer in graded_answers
    )


def test_cannot_view_another_users_attempt_results(client):
    owner_headers = register_and_login(
        client,
        email="results-owner@example.com",
    )
    quiz = create_quiz_with_questions(client, owner_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=owner_headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "Owner response.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert submit_response.status_code == 201
    attempt_id = submit_response.json()["id"]

    other_headers = register_and_login(
        client,
        email="results-other@example.com",
    )

    response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results"
        ),
        headers=other_headers,
    )

    assert response.status_code == 404


def test_get_quiz_attempt_history(client):
    headers = register_and_login(
        client,
        email="history@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert submit_response.status_code == 201

    response = client.get(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["attempt_id"] == submit_response.json()["id"]
    assert data[0]["score"] == 3
    assert data[0]["gradable_questions"] == 3
    assert data[0]["total_questions"] == 3
    assert data[0]["submitted_at"] is not None


def test_quiz_attempt_history_shows_multiple_attempts(client):
    headers = register_and_login(
        client,
        email="multiple-history@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    payload = {
        "answers": [
            {
                "question_id": quiz["multiple_choice"]["id"],
                "selected_choice_id": correct_choice["id"],
            },
            {
                "question_id": quiz["written"]["id"],
                "text_answer": "A variable stores a value.",
            },
            {
                "question_id": quiz["math"]["id"],
                "text_answer": "5",
            },
        ],
    }

    first_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json=payload,
    )
    second_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_user_can_view_own_attempt_history_for_another_users_quiz(client):
    owner_headers = register_and_login(
        client,
        email="history-owner@example.com",
    )
    quiz = create_quiz_with_questions(client, owner_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    taker_headers = register_and_login(
        client,
        email="history-taker@example.com",
    )

    submit_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=taker_headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert submit_response.status_code == 201

    response = client.get(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=taker_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["attempt_id"] == submit_response.json()["id"]
    assert data[0]["score"] == 3
    assert data[0]["gradable_questions"] == 3
    assert data[0]["total_questions"] == 3


def test_authenticated_user_can_submit_attempt_for_another_users_quiz(client):
    owner_headers = register_and_login(
        client,
        email="attempt-owner@example.com",
    )
    quiz = create_quiz_with_questions(client, owner_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    taker_headers = register_and_login(
        client,
        email="attempt-taker@example.com",
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=taker_headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "2x = 10, so x = 5.",
                },
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["quiz_id"] == quiz["quiz_id"]
    assert len(response.json()["answers"]) == 3


def test_can_submit_quiz_with_unanswered_questions(client):
    headers = register_and_login(
        client,
        email="unanswered-attempt@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": None,
                    "text_answer": None,
                },
                {
                    "question_id": quiz["written"]["id"],
                    "selected_choice_id": None,
                    "text_answer": None,
                },
                {
                    "question_id": quiz["math"]["id"],
                    "selected_choice_id": None,
                    "text_answer": None,
                },
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert len(data["answers"]) == 3


def test_submit_quiz_attempt_records_completion_audit(client, db):
    creator_headers = register_and_login(
        client,
        email="audit-creator@example.com",
    )

    quiz = create_quiz_with_questions(
        client,
        creator_headers,
    )

    taker_headers = register_and_login(
        client,
        email="audit-taker@example.com",
    )

    taker_response = client.get(
        "/api/v1/auth/me",
        headers=taker_headers,
    )
    assert taker_response.status_code == 200
    taker = taker_response.json()

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=taker_headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "2x = 10, so x = 5.",
                },
            ],
        },
    )

    assert response.status_code == 201

    audit_log = db.scalar(
        select(AuditLog).where(
            AuditLog.user_id == uuid.UUID(taker["id"]),
            AuditLog.quiz_id == uuid.UUID(quiz["quiz_id"]),
            AuditLog.action == "quiz_completed",
        )
    )

    assert audit_log is not None
    assert str(audit_log.user_id) == taker["id"]
    assert str(audit_log.quiz_id) == quiz["quiz_id"]
    assert audit_log.action == "quiz_completed"
    assert audit_log.quiz_title == "Quiz Attempt Test"
    assert audit_log.creator_name == "Attempt audit-creator"
    assert audit_log.created_at is not None


def test_guest_can_submit_quiz_without_persisting_attempt(client, db):
    creator_headers = register_and_login(
        client,
        email="guest-attempt-creator@example.com",
    )
    quiz = create_quiz_with_questions(
        client,
        creator_headers,
    )

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    attempts_before = db.scalar(
        select(func.count(QuizAttempt.id))
    ) or 0

    audit_logs_before = db.scalar(
        select(func.count(AuditLog.id))
    ) or 0

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts/guest",
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quiz_id"] == quiz["quiz_id"]
    assert data["total_questions"] == 3
    assert len(data["answers"]) == 3

    # Guest responses intentionally have no persistent attempt ID.
    assert "attempt_id" not in data

    attempts_after = db.scalar(
        select(func.count(QuizAttempt.id))
    ) or 0

    audit_logs_after = db.scalar(
        select(func.count(AuditLog.id))
    ) or 0

    assert attempts_after == attempts_before
    assert audit_logs_after == audit_logs_before


def test_guest_attempt_requires_every_quiz_question(client):
    creator_headers = register_and_login(
        client,
        email="guest-incomplete-creator@example.com",
    )
    quiz = create_quiz_with_questions(
        client,
        creator_headers,
    )

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts/guest",
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "An answer must be provided for every quiz question"
    )


def test_guest_can_submit_quiz_without_authentication(client):
    creator_headers = register_and_login(
        client,
        email="guest-quiz-creator@example.com",
    )
    quiz = create_quiz_with_questions(client, creator_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts/guest",
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quiz_id"] == quiz["quiz_id"]
    assert "attempt_id" not in data
    assert data["total_questions"] == 3
    assert len(data["answers"]) == 3


def test_guest_attempt_is_not_persisted(client, db):
    creator_headers = register_and_login(
        client,
        email="guest-no-persist-creator@example.com",
    )
    quiz = create_quiz_with_questions(client, creator_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    attempts_before = db.scalars(
        select(QuizAttempt).where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
    ).all()

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts/guest",
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": None,
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 200

    attempts_after = db.scalars(
        select(QuizAttempt).where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
    ).all()

    assert len(attempts_after) == len(attempts_before)


def test_guest_attempt_does_not_create_audit_log(client, db):
    creator_headers = register_and_login(
        client,
        email="guest-no-audit-creator@example.com",
    )
    quiz = create_quiz_with_questions(client, creator_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts/guest",
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": None,
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 200

    audit_logs = db.scalars(
        select(AuditLog).where(
            AuditLog.quiz_id == uuid.UUID(quiz["quiz_id"]),
            AuditLog.action == "quiz_completed",
        )
    ).all()

    assert audit_logs == []


def test_can_export_own_quiz_attempt_results_as_pdf(client):
    headers = register_and_login(
        client,
        email="pdf-export@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    attempt_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert attempt_response.status_code == 201

    attempt_id = attempt_response.json()["id"]

    response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results/pdf"
        ),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment;" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000


def test_cannot_export_another_users_quiz_attempt_results_pdf(client):
    owner_headers = register_and_login(
        client,
        email="pdf-owner@example.com",
    )
    quiz = create_quiz_with_questions(client, owner_headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    attempt_response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=owner_headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert attempt_response.status_code == 201
    attempt_id = attempt_response.json()["id"]

    other_user_headers = register_and_login(
        client,
        email="pdf-other-user@example.com",
    )

    response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results/pdf"
        ),
        headers=other_user_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz attempt not found"


def test_math_work_attempt_saves_whiteboard_image(client, db):
    headers = register_and_login(
        client,
        email="whiteboard-save@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    whiteboard_image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mNk+M/wHwAF/gL+X8Wz5QAAAABJRU5ErkJggg=="
    )

    cloudinary_url = (
        "https://res.cloudinary.com/test-cloud/image/upload/"
        "quiz-app/whiteboards/test-whiteboard.png"
    )

    with patch(
        "app.services.whiteboard_storage_service."
        "cloudinary.uploader.upload",
        return_value={"secure_url": cloudinary_url},
    ) as mock_upload:
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                        "whiteboard_image": whiteboard_image,
                    },
                ],
            },
        )

    assert response.status_code == 201
    mock_upload.assert_called_once()

    attempt_id = response.json()["id"]

    answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == uuid.UUID(attempt_id),
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["math"]["id"]),
        )
    )

    assert answer is not None
    assert answer.whiteboard_image_url == cloudinary_url

    results_response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results"
        ),
        headers=headers,
    )

    assert results_response.status_code == 200

    math_result = next(
        result
        for result in results_response.json()["answers"]
        if result["question_id"] == quiz["math"]["id"]
    )

    assert math_result["whiteboard_image_url"] == cloudinary_url


def test_saved_whiteboard_uses_cloudinary_url(client, db):
    headers = register_and_login(
        client,
        email="cloudinary-whiteboard@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    whiteboard_image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mNk+M/wHwAF/gL+X8Wz5QAAAABJRU5ErkJggg=="
    )

    cloudinary_url = (
        "https://res.cloudinary.com/test-cloud/image/upload/"
        "quiz-app/whiteboards/saved-whiteboard.png"
    )

    with patch(
        "app.services.whiteboard_storage_service."
        "cloudinary.uploader.upload",
        return_value={"secure_url": cloudinary_url},
    ) as mock_upload:
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                        "whiteboard_image": whiteboard_image,
                    },
                ],
            },
        )

    assert response.status_code == 201
    mock_upload.assert_called_once()

    attempt_id = response.json()["id"]

    answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == uuid.UUID(attempt_id),
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["math"]["id"]),
        )
    )

    assert answer is not None
    assert answer.whiteboard_image_url == cloudinary_url
    assert answer.whiteboard_image_url.startswith(
        "https://res.cloudinary.com/"
    )

    results_response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt_id}/results"
        ),
        headers=headers,
    )

    assert results_response.status_code == 200

    math_result = next(
        result
        for result in results_response.json()["answers"]
        if result["question_id"] == quiz["math"]["id"]
    )

    assert math_result["whiteboard_image_url"] == cloudinary_url


def test_written_answer_rejects_whiteboard_image(client):
    headers = register_and_login(
        client,
        email="written-whiteboard@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                    "whiteboard_image": (
                        "data:image/png;base64,"
                        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
                    ),
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_multiple_choice_rejects_whiteboard_image(client):
    headers = register_and_login(
        client,
        email="choice-whiteboard@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                    "whiteboard_image": (
                        "data:image/png;base64,"
                        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
                    ),
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_math_work_rejects_invalid_whiteboard_image(client):
    headers = register_and_login(
        client,
        email="invalid-whiteboard@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                    "whiteboard_image": "this-is-not-a-valid-image",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_math_work_without_whiteboard_is_allowed(client):
    headers = register_and_login(
        client,
        email="no-whiteboard@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": quiz["multiple_choice"]["id"],
                    "selected_choice_id": correct_choice["id"],
                },
                {
                    "question_id": quiz["written"]["id"],
                    "text_answer": "A variable stores a value.",
                },
                {
                    "question_id": quiz["math"]["id"],
                    "text_answer": "5",
                },
            ],
        },
    )

    assert response.status_code == 201


def test_correct_written_answer_saves_ai_grading_without_explanation(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="correct-written-ai@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    evaluation = AnswerEvaluationResponse(
        is_correct=True,
        explanation="The answer correctly explains the concept.",
    )

    with patch(
        "app.api.v1.attempts.evaluate_written_answer",
        return_value=evaluation,
    ) as mock_evaluate:
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_evaluate.assert_called_once_with(
        question_text=quiz["written"]["text"],
        submitted_answer="A variable stores a value.",
    )

    attempt = db.scalar(
        select(QuizAttempt)
        .where(QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"]))
        .order_by(QuizAttempt.submitted_at.desc())
    )
    assert attempt is not None

    written_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["written"]["id"]),
        )
    )

    assert written_answer is not None
    assert written_answer.ai_is_correct is True
    assert written_answer.ai_explanation is None
def test_incorrect_written_answer_saves_ai_grading_and_explanation(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="incorrect-written-ai@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    evaluation = AnswerEvaluationResponse(
        is_correct=False,
        explanation=(
            "A variable stores a value; it does not define a reusable "
            "block of code."
        ),
    )

    with patch(
        "app.api.v1.attempts.evaluate_written_answer",
        return_value=evaluation,
    ) as mock_evaluate:
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "It repeats code forever.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_evaluate.assert_called_once_with(
        question_text=quiz["written"]["text"],
        submitted_answer="It repeats code forever.",
    )

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    written_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["written"]["id"]),
        )
    )

    assert written_answer is not None
    assert written_answer.ai_is_correct is False
    assert written_answer.ai_explanation == (
        "A variable stores a value; it does not define a reusable "
        "block of code."
    )


def test_correct_multiple_choice_does_not_generate_ai_explanation(
    client,
):
    headers = register_and_login(
        client,
        email="correct-mc-ai@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    written_evaluation = AnswerEvaluationResponse(
        is_correct=True,
        explanation="The written answer is correct.",
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
            return_value=written_evaluation,
        ),
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                    },
                ],
            },
        )

    assert response.status_code == 201
    mock_explanation.assert_not_called()


def test_incorrect_multiple_choice_saves_ai_explanation(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="incorrect-mc-ai@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    incorrect_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if not choice["is_correct"]
    )

    written_evaluation = AnswerEvaluationResponse(
        is_correct=True,
        explanation="The written answer is correct.",
    )

    explanation = IncorrectAnswerExplanationResponse(
        explanation=(
            "The selected answer 3 is incorrect because 2 + 2 equals 4."
        ),
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
            return_value=written_evaluation,
        ),
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
            return_value=explanation,
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": incorrect_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_explanation.assert_called_once_with(
        question_text=quiz["multiple_choice"]["text"],
        submitted_answer="3",
        correct_answer="4",
    )

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    multiple_choice_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["multiple_choice"]["id"]),
        )
    )

    assert multiple_choice_answer is not None
    assert multiple_choice_answer.ai_explanation == (
        "The selected answer 3 is incorrect because 2 + 2 equals 4."
    )

    results_response = client.get(
        (
            f"/api/v1/quizzes/{quiz['quiz_id']}"
            f"/attempts/{attempt.id}/results"
        ),
        headers=headers,
    )

    assert results_response.status_code == 200

    multiple_choice_result = next(
        result
        for result in results_response.json()["answers"]
        if result["question_id"] == quiz["multiple_choice"]["id"]
    )

    assert multiple_choice_result["ai_explanation"] == (
        "The selected answer 3 is incorrect because 2 + 2 equals 4."
    )

    # Loading saved results must reuse the persisted explanation rather
    # than making another AI request.
    assert mock_explanation.call_count == 1


def test_correct_math_work_uses_deterministic_grading_without_ai(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="correct-math-deterministic@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    written_evaluation = AnswerEvaluationResponse(
        is_correct=True,
        explanation="The written answer is correct.",
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
            return_value=written_evaluation,
        ),
        patch(
            "app.api.v1.attempts.evaluate_math_answer",
        ) as mock_math_ai,
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "10 / 2",
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_math_ai.assert_not_called()
    mock_explanation.assert_not_called()

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    math_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["math"]["id"]),
        )
    )

    assert math_answer is not None
    assert math_answer.ai_is_correct is True
    assert math_answer.ai_explanation is None


def test_incorrect_math_work_uses_deterministic_grading_and_ai_explanation(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="incorrect-math-deterministic@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )

    written_evaluation = AnswerEvaluationResponse(
        is_correct=True,
        explanation="The written answer is correct.",
    )

    explanation = IncorrectAnswerExplanationResponse(
        explanation=(
            "The answer 4 is incorrect. Dividing both sides of "
            "2x = 10 by 2 gives x = 5."
        ),
    )

    whiteboard_image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mNk+M/wHwAF/gL+X8Wz5QAAAABJRU5ErkJggg=="
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
            return_value=written_evaluation,
        ),
        patch(
            "app.api.v1.attempts.evaluate_math_answer",
        ) as mock_math_ai,
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
            return_value=explanation,
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "4",
                        "whiteboard_image": whiteboard_image,
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_math_ai.assert_not_called()

    mock_explanation.assert_called_once_with(
        question_text=quiz["math"]["text"],
        submitted_answer="4",
        correct_answer="5",
        whiteboard_image=whiteboard_image,
    )

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz["quiz_id"])
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    math_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["math"]["id"]),
        )
    )

    assert math_answer is not None
    assert math_answer.ai_is_correct is False
    assert math_answer.ai_explanation == (
        "The answer 4 is incorrect. Dividing both sides of "
        "2x = 10 by 2 gives x = 5."
    )


def test_non_math_math_work_uses_ai_semantic_grading_when_correct(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="semantic-math-work@example.com",
    )

    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Semantic Math Work Test",
            "description": "Tests AI fallback for non-math answers.",
        },
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]

    question_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/math-work",
        headers=headers,
        json={
            "text": "What is the star at the center of our solar system?",
            "expected_answer": "The Sun",
        },
    )
    assert question_response.status_code == 201
    question = question_response.json()

    evaluation = MathAnswerEvaluationResponse(
        is_correct=True,
        explanation="The Sun is the star at the center of the solar system.",
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_math_answer",
            return_value=evaluation,
        ) as mock_math_ai,
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz_id}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": question["id"],
                        "text_answer": "sun",
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_math_ai.assert_called_once_with(
        question_text=question["text"],
        submitted_answer="sun",
        expected_answer="The Sun",
        whiteboard_image=None,
    )
    mock_explanation.assert_not_called()

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz_id)
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    math_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(question["id"]),
        )
    )

    assert math_answer is not None
    assert math_answer.ai_is_correct is True
    assert math_answer.ai_explanation is None


def test_non_math_math_work_uses_ai_semantic_grading_when_incorrect(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="semantic-math-work-incorrect@example.com",
    )

    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Semantic Math Work Incorrect Test",
            "description": "Tests incorrect AI fallback.",
        },
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]

    question_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/math-work",
        headers=headers,
        json={
            "text": "What is the star at the center of our solar system?",
            "expected_answer": "The Sun",
        },
    )
    assert question_response.status_code == 201
    question = question_response.json()

    evaluation = MathAnswerEvaluationResponse(
        is_correct=False,
        explanation=(
            "Jupiter is a planet, not a star. The Sun is the star "
            "at the center of our solar system."
        ),
    )

    whiteboard_image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mNk+M/wHwAF/gL+X8Wz5QAAAABJRU5ErkJggg=="
    )

    with (
        patch(
            "app.api.v1.attempts.evaluate_math_answer",
            return_value=evaluation,
        ) as mock_math_ai,
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
        ) as mock_explanation,
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz_id}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": question["id"],
                        "text_answer": "Jupiter",
                        "whiteboard_image": whiteboard_image,
                    },
                ],
            },
        )

    assert response.status_code == 201

    mock_math_ai.assert_called_once_with(
        question_text=question["text"],
        submitted_answer="Jupiter",
        expected_answer="The Sun",
        whiteboard_image=whiteboard_image,
    )

    # The AI evaluation already supplied the explanation,
    # so the separate explanation service should not run.
    mock_explanation.assert_not_called()

    attempt = db.scalar(
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == uuid.UUID(quiz_id)
        )
        .order_by(QuizAttempt.submitted_at.desc())
    )

    assert attempt is not None

    math_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == attempt.id,
            QuizAttemptAnswer.question_id
            == uuid.UUID(question["id"]),
        )
    )

    assert math_answer is not None
    assert math_answer.ai_is_correct is False
    assert math_answer.ai_explanation == (
        "Jupiter is a planet, not a star. The Sun is the star "
        "at the center of our solar system."
    )


def test_whiteboard_storage_failure_returns_503(client):
    headers = register_and_login(
        client,
        email="whiteboard-storage-failure@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)
    correct_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if choice["is_correct"]
    )
    whiteboard_image = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        "AAAADUlEQVR42mNk+M/wHwAF/gL+X8Wz5QAAAABJRU5ErkJggg=="
    )

    with patch(
        "app.services.whiteboard_storage_service."
        "cloudinary.uploader.upload",
        side_effect=RuntimeError("Cloudinary unavailable"),
    ):
        response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": correct_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                        "whiteboard_image": whiteboard_image,
                    },
                ],
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Whiteboard image storage is temporarily unavailable. "
        "Please try again."
    )


def test_historical_results_reuse_saved_ai_explanation(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="saved-explanation-history@example.com",
    )
    quiz = create_quiz_with_questions(client, headers)

    incorrect_choice = next(
        choice
        for choice in quiz["multiple_choice"]["answer_choices"]
        if not choice["is_correct"]
    )

    saved_explanation = (
        "The selected answer is incorrect. "
        "The correct answer is 4."
    )

    explanation = IncorrectAnswerExplanationResponse(
        explanation=saved_explanation,
    )

    with (
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
            return_value=explanation,
        ),
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
            return_value=AnswerEvaluationResponse(
                is_correct=True,
                explanation="Correct.",
            ),
        ),
    ):
        submit_response = client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=headers,
            json={
                "answers": [
                    {
                        "question_id": quiz["multiple_choice"]["id"],
                        "selected_choice_id": incorrect_choice["id"],
                    },
                    {
                        "question_id": quiz["written"]["id"],
                        "text_answer": "A variable stores a value.",
                    },
                    {
                        "question_id": quiz["math"]["id"],
                        "text_answer": "5",
                    },
                ],
            },
        )

    assert submit_response.status_code == 201
    attempt_id = submit_response.json()["id"]

    stored_answer = db.scalar(
        select(QuizAttemptAnswer).where(
            QuizAttemptAnswer.attempt_id == uuid.UUID(attempt_id),
            QuizAttemptAnswer.question_id
            == uuid.UUID(quiz["multiple_choice"]["id"]),
        )
    )

    assert stored_answer is not None
    assert stored_answer.ai_explanation == saved_explanation

    with (
        patch(
            "app.api.v1.attempts.generate_incorrect_answer_explanation",
        ) as mock_explanation,
        patch(
            "app.api.v1.attempts.evaluate_written_answer",
        ) as mock_written_ai,
        patch(
            "app.api.v1.attempts.evaluate_math_answer",
        ) as mock_math_ai,
    ):
        response = client.get(
            (
                f"/api/v1/quizzes/{quiz['quiz_id']}"
                f"/attempts/{attempt_id}/results"
            ),
            headers=headers,
        )

    assert response.status_code == 200

    result = next(
        answer
        for answer in response.json()["answers"]
        if answer["question_id"] == quiz["multiple_choice"]["id"]
    )

    assert result["is_correct"] is False
    assert result["ai_explanation"] == saved_explanation

    mock_explanation.assert_not_called()
    mock_written_ai.assert_not_called()
    mock_math_ai.assert_not_called()
