import uuid
from types import SimpleNamespace
from unittest.mock import ANY, patch

import pytest

from app.schemas.ai import (
    ChatbotCreatedQuizzesPlan,
    ChatbotPerformanceTrendPlan,
    ChatbotAttemptComparisonPlan,
    ChatbotPlan,
    ChatbotQuestionPerformancePlan,
    ChatbotStudyRecommendationPlan,
    ChatbotQueryFiltersPlan,
    ChatbotQueryPlan,
)
from app.services.chatbot_data_service import (
    ChatbotAttemptRow,
    ChatbotQuestionPerformanceRow,
)
from app.services.chatbot_service import (
    _parse_optional_datetime,
    _resolve_report_month,
    answer_chatbot_data_question,
)


def test_parse_optional_datetime_accepts_iso_datetime():
    result = _parse_optional_datetime(
        "2026-08-01T00:00:00+00:00"
    )

    assert result is not None
    assert result.year == 2026
    assert result.month == 8
    assert result.day == 1


def test_parse_optional_datetime_accepts_z_timezone():
    result = _parse_optional_datetime(
        "2026-08-01T00:00:00Z"
    )

    assert result is not None
    assert result.utcoffset() is not None


def test_parse_optional_datetime_rejects_invalid_value():
    with pytest.raises(
        ValueError,
        match="Invalid chatbot query datetime",
    ):
        _parse_optional_datetime("not-a-date")


def test_answer_chatbot_data_question_connects_planner_data_and_query():
    user_id = uuid.uuid4()
    python_id = uuid.uuid4()
    biology_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="query",
        query=ChatbotQueryPlan(
            metrics=[
                "attempt_count",
                "average_score",
            ],
            group_by="quiz",
            sort_by="attempt_count",
            sort_direction="desc",
            limit=20,
        ),
    )

    attempt_rows = [
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=python_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-10T12:00:00+00:00"
            ),
            score_percentage=100.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=python_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-11T12:00:00+00:00"
            ),
            score_percentage=50.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=biology_id,
            quiz_title="Biology",
            creator_name="Bob",
            category="Science",
            submitted_at=_parse_optional_datetime(
                "2026-08-12T12:00:00+00:00"
            ),
            score_percentage=90.0,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ) as mock_plan,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows",
            return_value=attempt_rows,
        ) as mock_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question=(
                "Give me my quizzes with creator, "
                "attempts and average score."
            ),
            current_date="2026-08-25",
        )

    mock_plan.assert_called_once_with(
        question=(
            "Give me my quizzes with creator, "
            "attempts and average score."
        ),
        current_date="2026-08-25",
    )

    mock_rows.assert_called_once()

    assert mock_rows.call_args.kwargs["user_id"] == user_id

    assert result.total_rows == 2
    assert result.rows[0]["quiz_title"] == "Python Basics"
    assert result.rows[0]["creator_name"] == "Alice"
    assert result.rows[0]["attempt_count"] == 2
    assert result.rows[0]["average_score"] == 75.0

    assert result.rows[1]["quiz_title"] == "Biology"
    assert result.rows[1]["attempt_count"] == 1
    assert result.rows[1]["average_score"] == 90.0


def test_answer_chatbot_data_question_applies_planned_filters():
    user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="query",
        query=ChatbotQueryPlan(
            metrics=["average_score"],
            group_by="quiz",
            filters=ChatbotQueryFiltersPlan(
                category="Programming",
                date_from="2026-08-01T00:00:00+00:00",
                date_to="2026-08-31T23:59:59+00:00",
            ),
            sort_by="average_score",
            sort_direction="desc",
        ),
    )

    attempt_rows = [
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-15T12:00:00+00:00"
            ),
            score_percentage=95.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_title="Biology",
            creator_name="Bob",
            category="Science",
            submitted_at=_parse_optional_datetime(
                "2026-08-15T12:00:00+00:00"
            ),
            score_percentage=100.0,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.get_user_attempt_rows",
            return_value=attempt_rows,
        ),
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question=(
                "What was my best Programming quiz "
                "this month?"
            ),
            current_date="2026-08-25",
        )

    assert result.total_rows == 1
    assert result.rows[0]["quiz_title"] == "Python"
    assert result.rows[0]["average_score"] == 95.0

def test_resolve_report_month_this_month():
    result = _resolve_report_month(
        current_date="2026-08-25",
        period="this_month",
    )

    assert result == (2026, 8)


def test_resolve_report_month_last_month():
    result = _resolve_report_month(
        current_date="2026-08-25",
        period="last_month",
    )

    assert result == (2026, 7)


def test_resolve_report_month_last_month_crosses_year():
    result = _resolve_report_month(
        current_date="2026-01-10",
        period="last_month",
    )

    assert result == (2025, 12)


def test_resolve_report_month_rejects_unsupported_period():
    with pytest.raises(
        ValueError,
        match="Unsupported chatbot report period",
    ):
        _resolve_report_month(
            current_date="2026-08-25",
            period="next_month",
        )

def test_answer_chatbot_data_question_handles_question_performance():
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()
    question_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="question_performance",
        question_performance=ChatbotQuestionPerformancePlan(
            quiz_title="Python Basics",
            limit=5,
        ),
    )

    question_rows = [
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-20T12:00:00+00:00"
            ),
            is_correct=False,
        ),
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-21T12:00:00+00:00"
            ),
            is_correct=False,
        ),
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-22T12:00:00+00:00"
            ),
            is_correct=True,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service."
            "get_user_question_performance_rows",
            return_value=question_rows,
        ) as mock_question_rows,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows",
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question=(
                "What questions do I keep getting wrong "
                "on Python Basics?"
            ),
            current_date="2026-08-25",
        )

    mock_question_rows.assert_called_once()
    mock_attempt_rows.assert_not_called()

    assert result.total_rows == 1
    assert result.rows[0]["quiz_title"] == "Python Basics"
    assert result.rows[0]["question_text"] == "What is a Python list?"
    assert result.rows[0]["attempt_count"] == 3
    assert result.rows[0]["correct_count"] == 1
    assert result.rows[0]["wrong_count"] == 2
    assert result.rows[0]["miss_rate"] == 66.67



def test_answer_chatbot_data_question_handles_performance_trend():
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="performance_trend",
        performance_trend=ChatbotPerformanceTrendPlan(
            quiz_title="Python Basics",
        ),
    )

    attempt_rows = [
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-01T12:00:00+00:00"
            ),
            score_percentage=60.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-20T12:00:00+00:00"
            ),
            score_percentage=85.0,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.get_user_attempt_rows",
            return_value=attempt_rows,
        ),
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="Am I improving at Python Basics?",
            current_date="2026-08-25",
        )

    assert result.total_rows == 1
    assert result.rows[0]["quiz_title"] == "Python Basics"
    assert result.rows[0]["attempt_count"] == 2
    assert result.rows[0]["first_score"] == 60.0
    assert result.rows[0]["latest_score"] == 85.0
    assert result.rows[0]["score_change"] == 25.0
    assert result.rows[0]["direction"] == "improving"


def test_answer_chatbot_data_question_handles_attempt_comparison():
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="attempt_comparison",
        attempt_comparison=ChatbotAttemptComparisonPlan(
            quiz_title="JavaScript Fundamentals",
            limit=2,
        ),
    )

    attempt_rows = [
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-10T12:00:00+00:00"
            ),
            score_percentage=50.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-20T12:00:00+00:00"
            ),
            score_percentage=80.0,
        ),
        ChatbotAttemptRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            creator_name="Alice",
            category="Programming",
            submitted_at=_parse_optional_datetime(
                "2026-08-22T12:00:00+00:00"
            ),
            score_percentage=90.0,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.get_user_attempt_rows",
            return_value=attempt_rows,
        ),
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question=(
                "Compare my last 2 attempts on "
                "JavaScript Fundamentals."
            ),
            current_date="2026-08-25",
        )

    assert result.total_rows == 2
    assert result.rows[0]["quiz_title"] == (
        "JavaScript Fundamentals"
    )
    assert result.rows[0]["score_percentage"] == 90.0
    assert result.rows[1]["score_percentage"] == 80.0

def test_answer_chatbot_data_question_handles_study_recommendation():
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()
    question_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="study_recommendation",
        study_recommendation=ChatbotStudyRecommendationPlan(
            quiz_title="Python Basics",
            limit=5,
        ),
    )

    question_rows = [
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-20T12:00:00+00:00"
            ),
            is_correct=False,
        ),
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-21T12:00:00+00:00"
            ),
            is_correct=False,
        ),
        ChatbotQuestionPerformanceRow(
            attempt_id=uuid.uuid4(),
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a Python list?",
            question_type="multiple_choice",
            submitted_at=_parse_optional_datetime(
                "2026-08-22T12:00:00+00:00"
            ),
            is_correct=True,
        ),
    ]

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service."
            "get_user_question_performance_rows",
            return_value=question_rows,
        ) as mock_question_rows,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="What should I study next?",
            current_date="2026-08-25",
        )

    mock_question_rows.assert_called_once()
    mock_attempt_rows.assert_not_called()

    assert result.total_rows == 1

    row = result.rows[0]

    assert row["quiz_title"] == "Python Basics"
    assert row["question_text"] == "What is a Python list?"
    assert row["attempt_count"] == 3
    assert row["wrong_count"] == 2
    assert row["miss_rate"] == 66.67
    assert row["priority"] == 1
    assert row["reason"]



def test_answer_chatbot_data_question_handles_created_quizzes():
    user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="created_quizzes",
        created_quizzes=ChatbotCreatedQuizzesPlan(
            operation="count",
        ),
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service."
            "count_user_created_quizzes",
            return_value=8,
        ) as mock_count,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
        patch(
            "app.services.chatbot_service."
            "get_user_question_performance_rows"
        ) as mock_question_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="How many quizzes have I created?",
            current_date="2026-08-25",
        )

    mock_count.assert_called_once_with(
        mock_count.call_args.args[0],
        user_id=user_id,
        visibility=None,
        category=None,
        title_search=None,    )
    mock_attempt_rows.assert_not_called()
    mock_question_rows.assert_not_called()

    assert result.columns == ["created_quiz_count"]
    assert result.total_rows == 1
    assert result.rows == [
        {
            "created_quiz_count": 8,
        }
    ]


def test_answer_chatbot_data_question_lists_created_quizzes():
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="created_quizzes",
        created_quizzes=ChatbotCreatedQuizzesPlan(
            operation="list",
            limit=5,
        ),
    )

    quiz = SimpleNamespace(
        id=quiz_id,
        title="Python Basics",
        category="Programming",
        visibility="public",
        created_at=_parse_optional_datetime(
            "2026-08-20T12:00:00+00:00"
        ),
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.list_user_created_quizzes",
            return_value=[quiz],
        ) as mock_list,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="Give me quizzes created by me",
            current_date="2026-08-25",
        )

    mock_list.assert_called_once_with(
        ANY,
        user_id=user_id,
        visibility=None,
        category=None,
        title_search=None,
        sort_direction="desc",        limit=5,
    )
    mock_attempt_rows.assert_not_called()

    assert result.total_rows == 1
    assert result.columns == [
        "quiz_id",
        "quiz_title",
        "category",
        "visibility",
        "created_at",
    ]

    row = result.rows[0]

    assert row["quiz_id"] == str(quiz_id)
    assert row["quiz_title"] == "Python Basics"
    assert row["category"] == "Programming"
    assert row["visibility"] == "public"
    assert row["created_at"] == "2026-08-20T12:00:00+00:00"


def test_answer_chatbot_data_question_filters_created_quizzes_by_visibility():
    user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="created_quizzes",
        created_quizzes=ChatbotCreatedQuizzesPlan(
            operation="list",
            visibility="public",
            limit=10,
        ),
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.list_user_created_quizzes",
            return_value=[],
        ) as mock_list,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="Give me only public quizzes created by me",
            current_date="2026-08-25",
        )

    mock_list.assert_called_once_with(
        mock_list.call_args.args[0],
        user_id=user_id,
        visibility="public",
        category=None,
        title_search=None,
        sort_direction="desc",        limit=10,
    )
    mock_attempt_rows.assert_not_called()

    assert result.total_rows == 0


def test_answer_chatbot_data_question_counts_followers():
    from app.schemas.ai import ChatbotUserConnectionsPlan

    user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="user_connections",
        user_connections=ChatbotUserConnectionsPlan(
            direction="followers",
            operation="count",
        ),
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.count_user_connections",
            return_value=7,
        ) as mock_count,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="How many followers do I have?",
            current_date="2026-08-25",
        )

    mock_count.assert_called_once_with(
        mock_count.call_args.args[0],
        user_id=user_id,
        direction="followers",
    )
    mock_attempt_rows.assert_not_called()

    assert result.columns == ["follower_count"]
    assert result.rows == [
        {
            "follower_count": 7,
        }
    ]
    assert result.total_rows == 1


def test_answer_chatbot_data_question_counts_following():
    from app.schemas.ai import ChatbotUserConnectionsPlan

    user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="user_connections",
        user_connections=ChatbotUserConnectionsPlan(
            direction="following",
            operation="count",
        ),
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.count_user_connections",
            return_value=4,
        ) as mock_count,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="How many people am I following?",
            current_date="2026-08-25",
        )

    mock_count.assert_called_once_with(
        mock_count.call_args.args[0],
        user_id=user_id,
        direction="following",
    )
    mock_attempt_rows.assert_not_called()

    assert result.columns == ["following_count"]
    assert result.rows == [
        {
            "following_count": 4,
        }
    ]
    assert result.total_rows == 1


def test_answer_chatbot_data_question_lists_followers():
    from types import SimpleNamespace

    from app.schemas.ai import ChatbotUserConnectionsPlan

    user_id = uuid.uuid4()
    follower_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="user_connections",
        user_connections=ChatbotUserConnectionsPlan(
            direction="followers",
            operation="list",
            limit=5,
        ),
    )

    follower = SimpleNamespace(
        id=follower_id,
        display_name="Follower One",
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.list_user_connections",
            return_value=[follower],
        ) as mock_list,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="Show my 5 followers",
            current_date="2026-08-25",
        )

    mock_list.assert_called_once_with(
        mock_list.call_args.args[0],
        user_id=user_id,
        direction="followers",
        limit=5,
    )
    mock_attempt_rows.assert_not_called()

    assert result.columns == [
        "user_id",
        "display_name",
    ]
    assert result.rows == [
        {
            "user_id": str(follower_id),
            "display_name": "Follower One",
        }
    ]
    assert result.total_rows == 1


def test_answer_chatbot_data_question_lists_following():
    from types import SimpleNamespace

    from app.schemas.ai import ChatbotUserConnectionsPlan

    user_id = uuid.uuid4()
    followed_user_id = uuid.uuid4()

    plan = ChatbotPlan(
        intent="user_connections",
        user_connections=ChatbotUserConnectionsPlan(
            direction="following",
            operation="list",
            limit=3,
        ),
    )

    followed_user = SimpleNamespace(
        id=followed_user_id,
        display_name="Person Followed",
    )

    with (
        patch(
            "app.services.chatbot_service.plan_chatbot_query",
            return_value=plan,
        ),
        patch(
            "app.services.chatbot_service.list_user_connections",
            return_value=[followed_user],
        ) as mock_list,
        patch(
            "app.services.chatbot_service.get_user_attempt_rows"
        ) as mock_attempt_rows,
    ):
        result = answer_chatbot_data_question(
            object(),
            user_id=user_id,
            question="Show 3 people I follow",
            current_date="2026-08-25",
        )

    mock_list.assert_called_once_with(
        mock_list.call_args.args[0],
        user_id=user_id,
        direction="following",
        limit=3,
    )
    mock_attempt_rows.assert_not_called()

    assert result.columns == [
        "user_id",
        "display_name",
    ]
    assert result.rows == [
        {
            "user_id": str(followed_user_id),
            "display_name": "Person Followed",
        }
    ]
    assert result.total_rows == 1
