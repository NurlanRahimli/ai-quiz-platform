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
    assert data["score"] == 2
    assert data["gradable_questions"] == 2
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

    assert results["written_answer"]["is_correct"] is None
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
    assert data["gradable_questions"] == 2
    assert data["total_questions"] == 3

    graded_answers = [
        answer
        for answer in data["answers"]
        if answer["is_correct"] is not None
    ]

    assert len(graded_answers) == 2
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
    assert data[0]["score"] == 2
    assert data[0]["gradable_questions"] == 2
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


def test_cannot_view_another_users_quiz_attempt_history(client):
    owner_headers = register_and_login(
        client,
        email="history-owner@example.com",
    )
    quiz = create_quiz_with_questions(client, owner_headers)

    other_headers = register_and_login(
        client,
        email="history-other@example.com",
    )

    response = client.get(
        f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
        headers=other_headers,
    )

    assert response.status_code == 404


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