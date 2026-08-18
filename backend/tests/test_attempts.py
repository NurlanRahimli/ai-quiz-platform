def register_and_login(
    client,
    email="attempt-user@example.com",
    password="Password123!",
):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": "Attempt User",
        },
    )
    assert register_response.status_code == 201

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