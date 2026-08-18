def register_and_login(
    client,
    email="questions@example.com",
    password="Testing123!",
):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Question User",
            "email": email,
            "password": password,
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
        ),
    }


def create_quiz(client, headers, title="Test Quiz"):
    response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": title,
            "description": "Quiz for question tests",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_create_multiple_choice_question(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
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
                {
                    "text": "5",
                    "is_correct": False,
                },
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["quiz_id"] == quiz_id
    assert data["text"] == "What is 2 + 2?"
    assert data["question_type"] == "multiple_choice"
    assert data["position"] == 1

    assert len(data["answer_choices"]) == 3

    assert data["answer_choices"][0]["text"] == "3"
    assert data["answer_choices"][0]["position"] == 1
    assert data["answer_choices"][0]["is_correct"] is False

    assert data["answer_choices"][1]["text"] == "4"
    assert data["answer_choices"][1]["position"] == 2
    assert data["answer_choices"][1]["is_correct"] is True

    assert data["answer_choices"][2]["text"] == "5"
    assert data["answer_choices"][2]["position"] == 3
    assert data["answer_choices"][2]["is_correct"] is False


def test_question_positions_increment(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    payload = {
        "text": "First question",
        "choices": [
            {
                "text": "Wrong",
                "is_correct": False,
            },
            {
                "text": "Correct",
                "is_correct": True,
            },
        ],
    }

    first_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json=payload,
    )

    second_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            **payload,
            "text": "Second question",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["position"] == 1
    assert second_response.json()["position"] == 2


def test_question_requires_at_least_two_choices(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "Invalid question",
            "choices": [
                {
                    "text": "Only choice",
                    "is_correct": True,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_question_requires_exactly_one_correct_answer(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    no_correct_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "No correct answer",
            "choices": [
                {
                    "text": "A",
                    "is_correct": False,
                },
                {
                    "text": "B",
                    "is_correct": False,
                },
            ],
        },
    )

    assert no_correct_response.status_code == 422

    multiple_correct_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "Too many correct answers",
            "choices": [
                {
                    "text": "A",
                    "is_correct": True,
                },
                {
                    "text": "B",
                    "is_correct": True,
                },
            ],
        },
    )

    assert multiple_correct_response.status_code == 422


def test_question_rejects_empty_text(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "   ",
            "choices": [
                {
                    "text": "A",
                    "is_correct": True,
                },
                {
                    "text": "B",
                    "is_correct": False,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_question_rejects_empty_choice(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "Valid question",
            "choices": [
                {
                    "text": "   ",
                    "is_correct": True,
                },
                {
                    "text": "Valid choice",
                    "is_correct": False,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_cannot_add_question_to_another_users_quiz(client):
    owner_headers = register_and_login(
        client,
        email="question-owner@example.com",
    )
    quiz_id = create_quiz(client, owner_headers)

    other_headers = register_and_login(
        client,
        email="question-other@example.com",
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=other_headers,
        json={
            "text": "Unauthorized question",
            "choices": [
                {
                    "text": "A",
                    "is_correct": True,
                },
                {
                    "text": "B",
                    "is_correct": False,
                },
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz not found"


def test_create_question_requires_authentication(client):
    response = client.post(
        "/api/v1/quizzes/00000000-0000-0000-0000-000000000000/questions",
        json={
            "text": "Unauthorized",
            "choices": [
                {
                    "text": "A",
                    "is_correct": True,
                },
                {
                    "text": "B",
                    "is_correct": False,
                },
            ],
        },
    )

    assert response.status_code in (401, 403)


def test_create_written_answer_question(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/written",
        headers=headers,
        json={
            "text": "Explain what a closure is in JavaScript.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["quiz_id"] == quiz_id
    assert data["text"] == "Explain what a closure is in JavaScript."
    assert data["question_type"] == "written_answer"
    assert data["position"] == 1
    assert data["answer_choices"] == []


def test_written_answer_question_rejects_empty_text(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/written",
        headers=headers,
        json={
            "text": "   ",
        },
    )

    assert response.status_code == 422


def test_cannot_add_written_question_to_another_users_quiz(client):
    owner_headers = register_and_login(
        client,
        email="written-owner@example.com",
    )
    quiz_id = create_quiz(client, owner_headers)

    other_headers = register_and_login(
        client,
        email="written-other@example.com",
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/written",
        headers=other_headers,
        json={
            "text": "Unauthorized written question",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz not found"


def test_create_written_question_requires_authentication(client):
    response = client.post(
        (
            "/api/v1/quizzes/"
            "00000000-0000-0000-0000-000000000000/"
            "questions/written"
        ),
        json={
            "text": "Unauthorized written question",
        },
    )

    assert response.status_code in (401, 403)


def test_multiple_choice_and_written_questions_share_positions(client):
    headers = register_and_login(client)
    quiz_id = create_quiz(client, headers)

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

    written_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions/written",
        headers=headers,
        json={
            "text": "Explain how you got your answer.",
        },
    )

    assert multiple_choice_response.status_code == 201
    assert written_response.status_code == 201

    assert multiple_choice_response.json()["position"] == 1
    assert written_response.json()["position"] == 2

    assert (
        multiple_choice_response.json()["question_type"]
        == "multiple_choice"
    )
    assert (
        written_response.json()["question_type"]
        == "written_answer"
    )