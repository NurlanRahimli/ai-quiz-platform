import pytest
from unittest.mock import patch

from app.schemas.chatbot import (
    ChatbotReportInsight,
    ChatbotReportResponse,
)
from app.services.chatbot_query_service import ChatbotQueryResult


def register_and_login(
    client,
    register_verified_user_helper,
    *,
    email="chatbot-api@example.com",
    password="StrongPass123!",
):
    register_verified_user_helper(
        client,
        email=email,
        password=password,
        display_name="Chatbot User",
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



def test_chatbot_requires_authentication(client):
    response = client.post(
        "/api/v1/chatbot",
        json={
            "message": "How many quizzes have I taken?",
        },
    )

    assert response.status_code == 401


def test_chatbot_rejects_empty_message(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )

    response = client.post(
        "/api/v1/chatbot",
        headers=headers,
        json={
            "message": "",
        },
    )

    assert response.status_code == 422


def test_chatbot_returns_single_metric_result(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )
    result = ChatbotQueryResult(
        columns=["quiz_count"],
        rows=[
            {
                "quiz_count": 7,
            }
        ],
        total_rows=1,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ) as mock_answer:
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "How many quizzes have I taken?",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "type": "text",
        "message": "You've taken 7 quizzes.",
        "columns": [],
        "rows": [],
        "total_rows": 0,
    }

    mock_answer.assert_called_once()

    call_kwargs = mock_answer.call_args.kwargs

    assert call_kwargs["question"] == (
        "How many quizzes have I taken?"
    )
    assert call_kwargs["user_id"] is not None
    assert call_kwargs["current_date"]


def test_chatbot_returns_table_result(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )
    result = ChatbotQueryResult(
        columns=[
            "quiz_id",
            "quiz_title",
            "creator_name",
            "category",
            "attempt_count",
            "average_score",
        ],
        rows=[
            {
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "creator_name": "Alice",
                "category": "Programming",
                "attempt_count": 4,
                "average_score": 87.5,
            },
            {
                "quiz_id": "quiz-2",
                "quiz_title": "Biology",
                "creator_name": "Bob",
                "category": "Science",
                "attempt_count": 2,
                "average_score": 75.0,
            },
        ],
        total_rows=2,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ):
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": (
                    "Give me the quizzes I have taken with "
                    "their creator, attempts and average."
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "table"
    assert body["message"] == "I found 2 results."
    assert body["total_rows"] == 2

    assert body["columns"] == [
        "quiz_id",
        "quiz_title",
        "creator_name",
        "category",
        "attempt_count",
        "average_score",
    ]

    assert body["rows"][0]["quiz_title"] == "Python Basics"
    assert body["rows"][0]["creator_name"] == "Alice"
    assert body["rows"][0]["attempt_count"] == 4
    assert body["rows"][0]["average_score"] == 87.5


def test_chatbot_passes_authenticated_user_to_service(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )
    result = ChatbotQueryResult(
        columns=["attempt_count"],
        rows=[
            {
                "attempt_count": 3,
            }
        ],
        total_rows=1,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ) as mock_answer:
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "How many attempts have I made?",
            },
        )

    assert response.status_code == 200

    call_kwargs = mock_answer.call_args.kwargs

    assert call_kwargs["user_id"] is not None

    call_args = mock_answer.call_args.args

    assert len(call_args) == 1

    db = call_args[0]
    user_id = call_kwargs["user_id"]

    assert db is not None
    assert user_id is not None

def test_chatbot_returns_monthly_report(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )

    result = ChatbotReportResponse(
        title="July 2026 Performance Report",
        message=(
            "Here's a summary of your quiz performance "
            "for this period."
        ),
        insights=[
            ChatbotReportInsight(
                status="positive",
                icon="chart-no-axes-combined",
                label="Average Score",
                value="82.5%",
                detail=(
                    "Up 7.5 points from the previous month."
                ),
            ),
            ChatbotReportInsight(
                status="negative",
                icon="triangle-alert",
                label="Needs Attention",
                value="Programming",
                detail="52% average score.",
            ),
        ],
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ) as mock_answer:
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "Give me my report for last month.",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "type": "report",
        "title": "July 2026 Performance Report",
        "message": (
            "Here's a summary of your quiz performance "
            "for this period."
        ),
        "insights": [
            {
                "status": "positive",
                "icon": "chart-no-axes-combined",
                "label": "Average Score",
                "value": "82.5%",
                "detail": (
                    "Up 7.5 points from the previous month."
                ),
            },
            {
                "status": "negative",
                "icon": "triangle-alert",
                "label": "Needs Attention",
                "value": "Programming",
                "detail": "52% average score.",
            },
        ],
    }

    call_kwargs = mock_answer.call_args.kwargs

    assert call_kwargs["question"] == (
        "Give me my report for last month."
    )
    assert call_kwargs["user_id"] is not None
    assert call_kwargs["current_date"]

def test_chatbot_returns_question_performance_table(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )

    result = ChatbotQueryResult(
        columns=[
            "quiz_id",
            "quiz_title",
            "question_id",
            "question_text",
            "attempt_count",
            "correct_count",
            "wrong_count",
            "miss_rate",
        ],
        rows=[
            {
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-1",
                "question_text": "What is a Python list?",
                "attempt_count": 3,
                "correct_count": 1,
                "wrong_count": 2,
                "miss_rate": 66.67,
            },
        ],
        total_rows=1,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ):
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": (
                    "What questions do I keep getting wrong?"
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "table"
    assert body["message"] == (
        "I found 1 question you've been missing most often."
    )
    assert body["total_rows"] == 1
    assert body["rows"][0]["question_text"] == (
        "What is a Python list?"
    )
    assert body["rows"][0]["wrong_count"] == 2
    assert body["rows"][0]["miss_rate"] == 66.67


def test_chatbot_returns_performance_trend_text(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )

    result = ChatbotQueryResult(
        columns=[
            "quiz_id",
            "quiz_title",
            "attempt_count",
            "first_score",
            "latest_score",
            "score_change",
            "direction",
        ],
        rows=[
            {
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "attempt_count": 6,
                "first_score": 0.0,
                "latest_score": 50.0,
                "score_change": 50.0,
                "direction": "improving",
            },
        ],
        total_rows=1,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ):
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": (
                    "Am I improving at JavaScript Fundamentals?"
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "text"
    assert body["message"] == (
        "Yes — you're improving on JavaScript Fundamentals. "
        "Your score increased from 0% to 50%, a 50-point "
        "improvement across 6 attempts."
    )


def test_chatbot_returns_attempt_comparison_table(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
    )

    result = ChatbotQueryResult(
        columns=[
            "attempt_id",
            "quiz_id",
            "quiz_title",
            "submitted_at",
            "score_percentage",
        ],
        rows=[
            {
                "attempt_id": "attempt-3",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-25T12:00:00+00:00",
                "score_percentage": 75.0,
            },
            {
                "attempt_id": "attempt-2",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-24T12:00:00+00:00",
                "score_percentage": 50.0,
            },
            {
                "attempt_id": "attempt-1",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-23T12:00:00+00:00",
                "score_percentage": 25.0,
            },
        ],
        total_rows=3,
    )

    with patch(
        "app.api.v1.chatbot.answer_chatbot_data_question",
        return_value=result,
    ):
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": (
                    "Compare my last 3 attempts on "
                    "JavaScript Fundamentals."
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["type"] == "table"
    assert body["message"] == (
        "Here are your 3 most recent graded attempts."
    )
    assert body["total_rows"] == 3
    assert body["rows"][0]["score_percentage"] == 75.0
    assert body["rows"][2]["score_percentage"] == 25.0




def test_chatbot_answers_irrelevant_question_without_ai_planner(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
        email="chatbot-irrelevant@example.com",
    )

    with patch(
        "app.services.chatbot_service.plan_chatbot_query"
    ) as mock_planner:
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "What's the weather today?",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "type": "text",
        "message": (
            "I can help with your QuizApp data, such as your "
            "quizzes, attempts, scores, performance, questions, "
            "study recommendations, reports, and connections."
        ),
        "columns": [],
        "rows": [],
        "total_rows": 0,
    }

    mock_planner.assert_not_called()


def test_chatbot_answers_garbage_without_ai_planner(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
        email="chatbot-garbage@example.com",
    )

    with patch(
        "app.services.chatbot_service.plan_chatbot_query"
    ) as mock_planner:
        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "asdfghjkl",
            },
        )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "I didn't understand that. Try asking me about your "
        "quizzes, attempts, scores, performance, questions, "
        "study recommendations, reports, or connections."
    )

    mock_planner.assert_not_called()


def test_chatbot_relevant_question_still_uses_ai_planner(
    client,
    register_verified_user_helper,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
        email="chatbot-relevant@example.com",
    )

    result = ChatbotQueryResult(
        columns=["average_score"],
        rows=[
            {
                "average_score": 85,
            }
        ],
        total_rows=1,
    )

    with patch(
        "app.services.chatbot_service.plan_chatbot_query"
    ) as mock_planner, patch(
        "app.services.chatbot_service.execute_chatbot_query",
        return_value=result,
    ):
        from app.schemas.ai import (
            ChatbotPlan,
            ChatbotQueryFiltersPlan,
            ChatbotQueryPlan,
        )

        mock_planner.return_value = ChatbotPlan(
            intent="query",
            query=ChatbotQueryPlan(
                metrics=["average_score"],
                filters=ChatbotQueryFiltersPlan(),
            ),
        )

        response = client.post(
            "/api/v1/chatbot",
            headers=headers,
            json={
                "message": "What is my average score?",
            },
        )

    assert response.status_code == 200
    mock_planner.assert_called_once()



@pytest.mark.parametrize(
    "message",
    [
        "followers",
        "my quizzes",
        "my scores",
        "performance",
        "What should I study?",
        "Which questions do I struggle with?",
        "Compare my recent attempts",
        "Give me my monthly report",
    ],
)
def test_chatbot_fast_path_preserves_relevant_questions(
    message,
):
    from app.services.chatbot_service import _instant_chatbot_response

    assert _instant_chatbot_response(message) is None


def test_chatbot_faq_returns_without_calling_ai_planner(
    client,
    register_verified_user_helper,
    monkeypatch,
):
    headers = register_and_login(
        client,
        register_verified_user_helper,
        email="chatbot-faq@example.com",
    )

    def fail_if_planner_is_called(*args, **kwargs):
        raise AssertionError(
            "AI planner should not be called for a recognized FAQ"
        )

    monkeypatch.setattr(
        "app.services.chatbot_service.plan_chatbot_query",
        fail_if_planner_is_called,
    )

    response = client.post(
        "/api/v1/chatbot",
        headers=headers,
        json={
            "message": "How do I create a quiz?",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["type"] == "text"
    assert "Create Quiz" in payload["message"]

