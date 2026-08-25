import uuid

from datetime import datetime, timedelta, timezone

from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from tests.conftest import register_verified_user


def set_attempt_submitted_at(
    db,
    *,
    attempt_id,
    submitted_at,
):
    attempt = db.get(
        QuizAttempt,
        uuid.UUID(attempt_id),
    )
    assert attempt is not None

    attempt.submitted_at = submitted_at
    db.commit()


def set_attempt_answers_ungraded(
    db,
    *,
    attempt_id,
):
    attempt_uuid = uuid.UUID(attempt_id)

    answers = (
        db.query(QuizAttemptAnswer)
        .filter(QuizAttemptAnswer.attempt_id == attempt_uuid)
        .all()
    )

    assert answers

    for answer in answers:
        answer.ai_is_correct = None
        answer.ai_explanation = None

    db.commit()


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
    category: str = "Programming",
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


def submit_attempt(
    client,
    headers,
    *,
    quiz,
    question,
    correct: bool,
):
    choice = next(
        choice
        for choice in question["answer_choices"]
        if choice["is_correct"] is correct
    )

    response = client.post(
        f"/api/v1/quizzes/{quiz['id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_choice_id": choice["id"],
                }
            ]
        },
    )
    assert response.status_code == 201

    return response.json()


def test_dashboard_requires_authentication(client):
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401


def test_empty_dashboard_stats(client):
    headers = register_and_login(
        client,
        email="dashboard-empty@example.com",
        display_name="Dashboard Empty",
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "stats": {
            "total_quizzes": 0,
            "average_score": None,
            "quizzes_taken": 0,
        },
        "recent_quizzes": [],
        "performance": [],
        "top_categories": [],
    }


def test_dashboard_total_quizzes_only_counts_owned_quizzes(client):
    first_headers = register_and_login(
        client,
        email="dashboard-owner@example.com",
        display_name="Dashboard Owner",
    )
    second_headers = register_and_login(
        client,
        email="dashboard-other@example.com",
        display_name="Dashboard Other",
    )

    create_quiz_with_question(
        client,
        first_headers,
        title="First Quiz",
    )
    create_quiz_with_question(
        client,
        first_headers,
        title="Second Quiz",
    )
    create_quiz_with_question(
        client,
        second_headers,
        title="Someone Else's Quiz",
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=first_headers,
    )

    assert response.status_code == 200
    assert response.json()["stats"]["total_quizzes"] == 2


def test_dashboard_repeated_attempts_count_one_quiz_taken(client):
    headers = register_and_login(
        client,
        email="dashboard-repeat@example.com",
        display_name="Dashboard Repeat",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Repeated Quiz",
    )

    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )
    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=False,
    )
    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    stats = response.json()["stats"]

    assert stats["quizzes_taken"] == 1
    assert stats["average_score"] == 66.67


def test_dashboard_recent_quizzes_returns_latest_five_unique_quizzes(
    client,
    db
):
    headers = register_and_login(
        client,
        email="dashboard-recent@example.com",
        display_name="Dashboard Recent",
    )

    created = []

    base_time = datetime(
        2026,
        8,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    for index in range(6):
        quiz, question = create_quiz_with_question(
            client,
            headers,
            title=f"Recent Quiz {index + 1}",
            category="Programming",
        )

        attempt = submit_attempt(
            client,
            headers,
            quiz=quiz,
            question=question,
            correct=True,
        )

        set_attempt_submitted_at(
            db,
            attempt_id=attempt["id"],
            submitted_at=base_time + timedelta(days=index),
        )

        created.append((quiz, question))

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    recent_quizzes = response.json()["recent_quizzes"]

    assert len(recent_quizzes) == 5

    returned_ids = {
        quiz["quiz_id"]
        for quiz in recent_quizzes
    }

    assert created[0][0]["id"] not in returned_ids


def test_dashboard_recent_quizzes_groups_repeated_attempts(client, db):
    headers = register_and_login(
        client,
        email="dashboard-recent-repeat@example.com",
        display_name="Dashboard Recent Repeat",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Repeated Recent Quiz",
        category="Mathematics",
    )

    first_attempt = submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=False,
    )

    latest_attempt = submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )

    set_attempt_submitted_at(
        db,
        attempt_id=first_attempt["id"],
        submitted_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    set_attempt_submitted_at(
        db,
        attempt_id=latest_attempt["id"],
        submitted_at=datetime(
            2026,
            8,
            2,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    recent_quizzes = response.json()["recent_quizzes"]

    assert len(recent_quizzes) == 1

    recent_quiz = recent_quizzes[0]

    assert recent_quiz["quiz_id"] == quiz["id"]
    assert recent_quiz["quiz_title"] == "Repeated Recent Quiz"
    assert recent_quiz["quiz_category"] == "Mathematics"
    assert recent_quiz["latest_attempt_id"] == latest_attempt["id"]
    assert recent_quiz["score_percentage"] == 100.0


def test_dashboard_performance_returns_scores_and_running_average(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="dashboard-performance@example.com",
        display_name="Dashboard Performance",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Performance Quiz",
        category="Programming",
    )

    base_time = datetime(
        2026,
        8,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    attempts = [
        submit_attempt(
            client,
            headers,
            quiz=quiz,
            question=question,
            correct=True,
        ),
        submit_attempt(
            client,
            headers,
            quiz=quiz,
            question=question,
            correct=False,
        ),
        submit_attempt(
            client,
            headers,
            quiz=quiz,
            question=question,
            correct=True,
        ),
    ]

    for index, attempt in enumerate(attempts):
        set_attempt_submitted_at(
            db,
            attempt_id=attempt["id"],
            submitted_at=base_time + timedelta(days=index),
        )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    performance = response.json()["performance"]

    assert len(performance) == 3

    assert [point["score"] for point in performance] == [
        100.0,
        0.0,
        100.0,
    ]

    assert [
        point["average_score"]
        for point in performance
    ] == [
        100.0,
        50.0,
        66.67,
    ]

    submitted_at_values = [
        point["submitted_at"]
        for point in performance
    ]

    assert submitted_at_values == sorted(
        submitted_at_values
    )


def test_dashboard_performance_excludes_attempts_older_than_one_year(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="dashboard-performance-year@example.com",
        display_name="Dashboard Performance Year",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Performance Year Quiz",
        category="Programming",
    )

    old_attempt = submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )

    recent_attempt = submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=False,
    )

    now = datetime.now(timezone.utc)

    set_attempt_submitted_at(
        db,
        attempt_id=old_attempt["id"],
        submitted_at=now - timedelta(days=366),
    )

    set_attempt_submitted_at(
        db,
        attempt_id=recent_attempt["id"],
        submitted_at=now - timedelta(days=10),
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    performance = response.json()["performance"]

    assert len(performance) == 1
    assert performance[0]["score"] == 0.0
    assert performance[0]["average_score"] == 0.0


def create_written_quiz(
    client,
    headers,
    *,
    title: str,
    category: str = "Programming",
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
        f"/api/v1/quizzes/{quiz['id']}/questions/written",
        headers=headers,
        json={
            "text": f"Explain {title}.",
        },
    )
    assert question_response.status_code == 201

    return quiz, question_response.json()


def submit_written_attempt(
    client,
    headers,
    *,
    quiz,
    question,
):
    response = client.post(
        f"/api/v1/quizzes/{quiz['id']}/attempts",
        headers=headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "text_answer": "This is my written response.",
                }
            ]
        },
    )
    assert response.status_code == 201

    return response.json()


def test_dashboard_performance_excludes_non_gradable_attempts(
    client,
    db,
):
    headers = register_and_login(
        client,
        email="dashboard-performance-ungraded@example.com",
        display_name="Dashboard Performance Ungraded",
    )

    graded_quiz, graded_question = create_quiz_with_question(
        client,
        headers,
        title="Graded Performance Quiz",
    )

    written_quiz, written_question = create_written_quiz(
        client,
        headers,
        title="Written Performance Quiz",
    )

    submit_attempt(
        client,
        headers,
        quiz=graded_quiz,
        question=graded_question,
        correct=True,
    )

    written_attempt = submit_written_attempt(
        client,
        headers,
        quiz=written_quiz,
        question=written_question,
    )

    set_attempt_answers_ungraded(
        db,
        attempt_id=written_attempt["id"],
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    performance = response.json()["performance"]

    assert len(performance) == 1
    assert performance[0]["score"] == 100.0
    assert performance[0]["average_score"] == 100.0


def test_dashboard_top_categories_rank_by_attempt_count_and_limit_to_three(
    client,
):
    headers = register_and_login(
        client,
        email="dashboard-categories@example.com",
        display_name="Dashboard Categories",
    )

    category_attempts = [
        ("Programming", 4),
        ("Mathematics", 3),
        ("Science", 2),
        ("History", 1),
    ]

    for category, attempt_count in category_attempts:
        quiz, question = create_quiz_with_question(
            client,
            headers,
            title=f"{category} Quiz",
            category=category,
        )

        for _ in range(attempt_count):
            submit_attempt(
                client,
                headers,
                quiz=quiz,
                question=question,
                correct=True,
            )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    top_categories = response.json()["top_categories"]

    assert len(top_categories) == 3

    assert [
        category["category"]
        for category in top_categories
    ] == [
        "Programming",
        "Mathematics",
        "Science",
    ]

    assert [
        category["attempt_count"]
        for category in top_categories
    ] == [4, 3, 2]

    assert all(
        category["average_score"] == 100.0
        for category in top_categories
    )


def test_dashboard_top_category_uses_average_of_attempt_percentages(
    client,
):
    headers = register_and_login(
        client,
        email="dashboard-category-average@example.com",
        display_name="Dashboard Category Average",
    )

    quiz, question = create_quiz_with_question(
        client,
        headers,
        title="Mathematics Quiz",
        category="Mathematics",
    )

    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )

    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=True,
    )

    submit_attempt(
        client,
        headers,
        quiz=quiz,
        question=question,
        correct=False,
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    top_categories = response.json()["top_categories"]

    assert len(top_categories) == 1

    category = top_categories[0]

    assert category["category"] == "Mathematics"
    assert category["attempt_count"] == 3
    assert category["average_score"] == 66.67