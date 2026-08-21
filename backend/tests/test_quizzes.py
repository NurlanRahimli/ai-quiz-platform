def register_and_login(
    client,
    email="quiz@example.com",
    password="Testing123!",
):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Quiz User",
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

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_quiz(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Python Basics",
            "description": "A quiz about Python fundamentals",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Python Basics"
    assert data["description"] == "A quiz about Python fundamentals"
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_quiz_requires_authentication(client):
    response = client.post(
        "/api/v1/quizzes",
        json={
            "title": "Unauthorized Quiz",
        },
    )

    assert response.status_code in (401, 403)


def test_create_quiz_rejects_empty_title(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "   ",
        },
    )

    assert response.status_code == 422


def test_list_quizzes_returns_only_current_users_quizzes(client):
    user_a_headers = register_and_login(
        client,
        email="user-a@example.com",
    )

    client.post(
        "/api/v1/quizzes",
        headers=user_a_headers,
        json={"title": "User A Quiz"},
    )

    user_b_headers = register_and_login(
        client,
        email="user-b@example.com",
    )

    client.post(
        "/api/v1/quizzes",
        headers=user_b_headers,
        json={"title": "User B Quiz"},
    )

    response = client.get(
        "/api/v1/quizzes",
        headers=user_a_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "User A Quiz"


def test_get_quiz(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Math Quiz",
            "description": "Basic mathematics",
        },
    )

    quiz_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == quiz_id
    assert response.json()["title"] == "Math Quiz"


def test_update_quiz(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "Old Title",
            "description": "Old description",
        },
    )

    quiz_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/quizzes/{quiz_id}",
        headers=headers,
        json={
            "title": "New Title",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["description"] == "Old description"


def test_delete_quiz(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={"title": "Delete Me"},
    )

    quiz_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/quizzes/{quiz_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_user_cannot_get_another_users_quiz(client):
    user_a_headers = register_and_login(
        client,
        email="owner@example.com",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=user_a_headers,
        json={"title": "Private Quiz"},
    )

    quiz_id = create_response.json()["id"]

    user_b_headers = register_and_login(
        client,
        email="other@example.com",
    )

    response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=user_b_headers,
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_quiz(client):
    user_a_headers = register_and_login(
        client,
        email="update-owner@example.com",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=user_a_headers,
        json={"title": "Private Quiz"},
    )

    quiz_id = create_response.json()["id"]

    user_b_headers = register_and_login(
        client,
        email="update-other@example.com",
    )

    response = client.patch(
        f"/api/v1/quizzes/{quiz_id}",
        headers=user_b_headers,
        json={"title": "Stolen Quiz"},
    )

    assert response.status_code == 404

    owner_response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=user_a_headers,
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == "Private Quiz"


def test_user_cannot_delete_another_users_quiz(client):
    user_a_headers = register_and_login(
        client,
        email="delete-owner@example.com",
    )

    create_response = client.post(
        "/api/v1/quizzes",
        headers=user_a_headers,
        json={"title": "Private Quiz"},
    )

    quiz_id = create_response.json()["id"]

    user_b_headers = register_and_login(
        client,
        email="delete-other@example.com",
    )

    response = client.delete(
        f"/api/v1/quizzes/{quiz_id}",
        headers=user_b_headers,
    )

    assert response.status_code == 404

    owner_response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=user_a_headers,
    )

    assert owner_response.status_code == 200


def test_get_quiz_includes_questions(client):
    headers = register_and_login(
        client,
        email="quiz-detail@example.com",
    )

    create_quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "JavaScript Quiz",
            "description": "Quiz editing test",
        },
    )

    assert create_quiz_response.status_code == 201
    quiz_id = create_quiz_response.json()["id"]

    mc_response = client.post(
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
            "text": "Explain closures.",
        },
    )

    assert mc_response.status_code == 201
    assert written_response.status_code == 201

    response = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "JavaScript Quiz"
    assert len(data["questions"]) == 2

    assert data["questions"][0]["position"] == 1
    assert data["questions"][0]["question_type"] == "multiple_choice"
    assert data["questions"][0]["text"] == "What is 2 + 2?"
    assert len(data["questions"][0]["answer_choices"]) == 2

    assert data["questions"][1]["position"] == 2
    assert data["questions"][1]["question_type"] == "written_answer"
    assert data["questions"][1]["text"] == "Explain closures."
    assert data["questions"][1]["answer_choices"] == []


def test_take_quiz_does_not_expose_correct_answers(client):
    headers = register_and_login(
        client,
        email="quiz-taker@example.com",
    )

    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": "JavaScript Quiz",
            "description": "Test your JavaScript knowledge",
        },
    )

    quiz_id = quiz_response.json()["id"]

    question_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=headers,
        json={
            "text": "Which keyword declares a block-scoped variable?",
            "choices": [
                {
                    "text": "let",
                    "is_correct": True,
                },
                {
                    "text": "define",
                    "is_correct": False,
                },
            ],
        },
    )

    assert question_response.status_code == 201

    response = client.get(
        f"/api/v1/quizzes/{quiz_id}/take",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "JavaScript Quiz"
    assert len(data["questions"]) == 1

    question = data["questions"][0]

    assert question["question_type"] == "multiple_choice"
    assert len(question["answer_choices"]) == 2

    for choice in question["answer_choices"]:
        assert "is_correct" not in choice


def test_authenticated_user_can_take_another_users_quiz(client):
    owner_headers = register_and_login(
        client,
        email="take-owner@example.com",
    )

    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=owner_headers,
        json={
            "title": "Shared Quiz",
            "description": "A quiz another user can take",
        },
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json()["id"]

    question_response = client.post(
        f"/api/v1/quizzes/{quiz_id}/questions",
        headers=owner_headers,
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

    taker_headers = register_and_login(
        client,
        email="take-other@example.com",
    )

    response = client.get(
        f"/api/v1/quizzes/{quiz_id}/take",
        headers=taker_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == quiz_id