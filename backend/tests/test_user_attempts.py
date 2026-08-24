from tests.conftest import register_verified_user

def register_and_login(
    client,
    *,
    email: str,
    display_name: str,
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


def create_quiz_with_question(
    client,
    headers,
    *,
    title: str,
    category: str,
):
    quiz_response = client.post(
        "/api/v1/quizzes",
        headers=headers,
        json={
            "title": title,
            "category": category,
            "visibility": "public",
        },
    )
    assert quiz_response.status_code == 201

    quiz = quiz_response.json()

    question_response = client.post(
        f"/api/v1/quizzes/{quiz['id']}/questions",
        headers=headers,
        json={
            "text": f"{title} question",
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
        },
    )
    assert question_response.status_code == 201

    return quiz, question_response.json()


def submit_correct_attempt(
    client,
    headers,
    *,
    quiz,
    question,
):
    correct_choice = next(
        choice
        for choice in question["answer_choices"]
        if choice["is_correct"]
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_choice_id": correct_choice["id"],
                }
            ]
        },
    )

    assert response.status_code == 201

    return response.json()


def test_get_current_users_attempts_only(client):
    first_headers = register_and_login(
        client,
        email="attempts-first@example.com",
        display_name="First User",
    )

    second_headers = register_and_login(
        client,
        email="attempts-second@example.com",
        display_name="Second User",
    )

    python_quiz, python_question = create_quiz_with_question(
        client,
        first_headers,
        title="Python Basics",
        category="Programming",
    )

    history_quiz, history_question = create_quiz_with_question(
        client,
        first_headers,
        title="World History",
        category="History",
    )

    javascript_quiz, javascript_question = (
        create_quiz_with_question(
            client,
            second_headers,
            title="JavaScript Basics",
            category="Programming",
        )
    )

    submit_correct_attempt(
        client,
        first_headers,
        quiz=python_quiz,
        question=python_question,
    )

    submit_correct_attempt(
        client,
        first_headers,
        quiz=history_quiz,
        question=history_question,
    )

    submit_correct_attempt(
        client,
        second_headers,
        quiz=javascript_quiz,
        question=javascript_question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=first_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1
    assert len(data["quizzes"]) == 2

    returned_quiz_ids = {
        quiz["quiz_id"]
        for quiz in data["quizzes"]
    }

    titles = {
        quiz["quiz_title"]
        for quiz in data["quizzes"]
    }

    assert titles == {
        "Python Basics",
        "World History",
    }

    assert "JavaScript Basics" not in titles

    for quiz in data["quizzes"]:
        assert quiz["latest_score"] == 1
        assert quiz["latest_gradable_questions"] == 1
        assert quiz["latest_total_questions"] == 1
        assert quiz["attempt_count"] == 1
        assert quiz["quiz_id"]
        assert quiz["latest_attempt_id"]
        assert quiz["latest_submitted_at"]


def test_user_attempts_are_paginated_newest_first(client):
    headers = register_and_login(
        client,
        email="attempt-pagination@example.com",
        display_name="Pagination User",
    )

    created_quizzes = []

    for index in range(12):
        quiz, question = create_quiz_with_question(
            client,
            headers,
            title=f"Pagination Quiz {index + 1}",
            category="Programming",
        )

        submit_correct_attempt(
            client,
            headers,
            quiz=quiz,
            question=question,
        )

        created_quizzes.append(quiz)

    first_response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "page": 1,
            "page_size": 10,
        },
    )

    assert first_response.status_code == 200

    first_page = first_response.json()

    assert first_page["total"] == 12
    assert first_page["page"] == 1
    assert first_page["page_size"] == 10
    assert first_page["total_pages"] == 2
    assert len(first_page["quizzes"]) == 10

    second_response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "page": 2,
            "page_size": 10,
        },
    )

    assert second_response.status_code == 200

    second_page = second_response.json()

    assert second_page["total"] == 12
    assert second_page["page"] == 2
    assert second_page["page_size"] == 10
    assert second_page["total_pages"] == 2
    assert len(second_page["quizzes"]) == 2

    first_page_ids = {
        quiz["quiz_id"]
        for quiz in first_page["quizzes"]
    }

    second_page_ids = {
        quiz["quiz_id"]
        for quiz in second_page["quizzes"]
    }

    assert first_page_ids.isdisjoint(second_page_ids)

    returned_quizzes = (
        first_page["quizzes"]
        + second_page["quizzes"]
    )

    returned_ids = {
        quiz["quiz_id"]
        for quiz in returned_quizzes
    }

    created_ids = {
        quiz["id"]
        for quiz in created_quizzes
    }

    assert returned_ids == created_ids

    latest_submitted_times = [
        quiz["latest_submitted_at"]
        for quiz in returned_quizzes
    ]

    assert latest_submitted_times == sorted(
        latest_submitted_times,
        reverse=True,
    )


def test_user_attempts_can_be_searched_by_quiz_title(client):
    headers = register_and_login(
        client,
        email="attempt-search@example.com",
        display_name="Search User",
    )

    python_quiz, python_question = create_quiz_with_question(
        client,
        headers,
        title="Python Fundamentals",
        category="Programming",
    )

    history_quiz, history_question = create_quiz_with_question(
        client,
        headers,
        title="World History",
        category="History",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=python_quiz,
        question=python_question,
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=history_quiz,
        question=history_question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "search": "python",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1
    assert data["quizzes"][0]["quiz_title"] == "Python Fundamentals"


def test_user_attempt_search_is_case_insensitive_and_partial(client):
    headers = register_and_login(
        client,
        email="attempt-partial-search@example.com",
        display_name="Partial Search User",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Python Fundamentals",
        category="Programming",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "search": "FUNDA",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1
    assert data["quizzes"][0]["quiz_title"] == "Python Fundamentals"


def test_user_attempts_can_be_filtered_by_category(client):
    headers = register_and_login(
        client,
        email="attempt-category-filter@example.com",
        display_name="Category Filter User",
    )

    python_quiz, python_question = create_quiz_with_question(
        client,
        headers,
        title="Python Basics",
        category="Programming",
    )

    history_quiz, history_question = create_quiz_with_question(
        client,
        headers,
        title="World History",
        category="History",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=python_quiz,
        question=python_question,
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=history_quiz,
        question=history_question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "category": "Programming",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1
    assert data["quizzes"][0]["quiz_title"] == "Python Basics"
    assert data["quizzes"][0]["quiz_category"] == "Programming"


def test_user_attempt_search_and_category_work_together(client):
    headers = register_and_login(
        client,
        email="attempt-combined-filter@example.com",
        display_name="Combined Filter User",
    )

    python_quiz, python_question = create_quiz_with_question(
        client,
        headers,
        title="Python Fundamentals",
        category="Programming",
    )

    history_quiz, history_question = create_quiz_with_question(
        client,
        headers,
        title="Python History",
        category="History",
    )

    javascript_quiz, javascript_question = create_quiz_with_question(
        client,
        headers,
        title="JavaScript Fundamentals",
        category="Programming",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=python_quiz,
        question=python_question,
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=history_quiz,
        question=history_question,
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=javascript_quiz,
        question=javascript_question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "search": "python",
            "category": "Programming",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1

    quiz = data["quizzes"][0]

    assert quiz["quiz_title"] == "Python Fundamentals"
    assert quiz["quiz_category"] == "Programming"


def test_user_attempts_can_be_filtered_by_score_range(client):
    headers = register_and_login(
        client,
        email="attempt-score-filter@example.com",
        display_name="Score Filter User",
    )

    perfect_quiz, perfect_question = create_quiz_with_question(
        client,
        headers,
        title="Perfect Score Quiz",
        category="Programming",
    )

    low_quiz, low_question = create_quiz_with_question(
        client,
        headers,
        title="Low Score Quiz",
        category="Programming",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=perfect_quiz,
        question=perfect_question,
    )

    wrong_choice = next(
        choice
        for choice in low_question["answer_choices"]
        if not choice["is_correct"]
    )

    wrong_response = client.post(
        f"/api/v1/quizzes/{low_quiz['id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": low_question["id"],
                    "selected_choice_id": wrong_choice["id"],
                }
            ]
        },
    )

    assert wrong_response.status_code == 201

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "score_range": "90-100",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1

    quiz = data["quizzes"][0]

    assert quiz["quiz_title"] == "Perfect Score Quiz"
    assert quiz["latest_score"] == 1
    assert quiz["latest_gradable_questions"] == 1
    assert quiz["latest_total_questions"] == 1


def test_user_attempts_can_be_filtered_by_date(client):
    headers = register_and_login(
        client,
        email="attempt-date-filter@example.com",
        display_name="Date Filter User",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Date Filter Quiz",
        category="Programming",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "date_from": "2000-01-01",
            "date_to": "2100-01-01",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1
    assert data["quizzes"][0]["quiz_title"] == "Date Filter Quiz"

    excluded_response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "date_from": "2000-01-01",
            "date_to": "2000-01-02",
        },
    )

    assert excluded_response.status_code == 200

    excluded_data = excluded_response.json()

    assert excluded_data["total"] == 0
    assert excluded_data["quizzes"] == []


def test_user_attempts_reject_invalid_date_range(client):
    headers = register_and_login(
        client,
        email="attempt-invalid-date@example.com",
        display_name="Invalid Date User",
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "date_from": "2026-08-23",
            "date_to": "2026-08-20",
        },
    )

    assert response.status_code == 422


def test_user_attempts_reject_invalid_score_range(client):
    headers = register_and_login(
        client,
        email="attempt-invalid-score@example.com",
        display_name="Invalid Score User",
    )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
        params={
            "score_range": "invalid-range",
        },
    )

    assert response.status_code == 422


def test_user_attempts_groups_multiple_attempts_by_quiz(client):
    headers = register_and_login(
        client,
        email="attempt-grouping@example.com",
        display_name="Grouping User",
    )

    python_quiz, python_question = create_quiz_with_question(
        client,
        headers,
        title="Python Fundamentals",
        category="Programming",
    )

    history_quiz, history_question = create_quiz_with_question(
        client,
        headers,
        title="World History",
        category="History",
    )

    for _ in range(3):
        submit_correct_attempt(
            client,
            headers,
            quiz=python_quiz,
            question=python_question,
        )

    for _ in range(2):
        submit_correct_attempt(
            client,
            headers,
            quiz=history_quiz,
            question=history_question,
        )

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["quizzes"]) == 2

    quizzes_by_id = {
        quiz["quiz_id"]: quiz
        for quiz in data["quizzes"]
    }

    python_item = quizzes_by_id[python_quiz["id"]]
    history_item = quizzes_by_id[history_quiz["id"]]

    assert python_item["quiz_title"] == "Python Fundamentals"
    assert python_item["quiz_category"] == "Programming"
    assert python_item["attempt_count"] == 3
    assert python_item["latest_score"] == 1
    assert python_item["latest_gradable_questions"] == 1
    assert python_item["latest_total_questions"] == 1

    assert history_item["quiz_title"] == "World History"
    assert history_item["quiz_category"] == "History"
    assert history_item["attempt_count"] == 2


def test_user_attempt_quiz_returns_average_score(client):
    headers = register_and_login(
        client,
        email="attempt-average@example.com",
        display_name="Average Score User",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Average Score Quiz",
        category="Programming",
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
    )

    submit_correct_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
    )

    wrong_choice = next(
        choice
        for choice in question["answer_choices"]
        if not choice["is_correct"]
    )

    wrong_response = client.post(
        f"/api/v1/quizzes/{quiz['id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_choice_id": wrong_choice["id"],
                }
            ]
        },
    )

    assert wrong_response.status_code == 201

    response = client.get(
        "/api/v1/attempts",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["quizzes"]) == 1

    quiz_item = data["quizzes"][0]

    assert quiz_item["quiz_id"] == quiz["id"]
    assert quiz_item["attempt_count"] == 3
    assert quiz_item["average_score"] == 66.67