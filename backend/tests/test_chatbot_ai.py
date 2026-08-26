from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.schemas.ai import (
    ChatbotPerformanceTrendPlan,
    ChatbotAttemptComparisonPlan,
    ChatbotMonthlyReportPlan,
    ChatbotPlan,
    ChatbotQueryPlan,
    ChatbotQuestionPerformancePlan,
    ChatbotStudyRecommendationPlan,
)
from app.services.ai_service import plan_chatbot_query


def test_plan_chatbot_query_returns_structured_plan():
    parsed_result = ChatbotPlan(
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

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question=(
                "Give me the quizzes I have taken with "
                "creator, attempts and average score."
            ),
            current_date="2026-08-25",
        )

    assert result == parsed_result
    assert result.intent == "query"
    assert result.query is not None
    assert result.monthly_report is None

    assert result.query.metrics == [
        "attempt_count",
        "average_score",
    ]
    assert result.query.group_by == "quiz"
    assert result.query.sort_by == "attempt_count"
    assert result.query.sort_direction == "desc"
    assert result.query.limit == 20

    mock_client.responses.parse.assert_called_once()

    call_kwargs = mock_client.responses.parse.call_args.kwargs

    assert call_kwargs["model"] == "gpt-5-mini"
    assert call_kwargs["text_format"] is ChatbotPlan

    messages = call_kwargs["input"]

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "2026-08-25" in messages[1]["content"]
    assert "creator, attempts and average score" in messages[1]["content"]


def test_plan_chatbot_query_rejects_missing_result():
    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = None

        with pytest.raises(
            RuntimeError,
            match="OpenAI did not return a chatbot query plan",
        ):
            plan_chatbot_query(
                question="How many quizzes have I taken?",
                current_date="2026-08-25",
            )


@patch("app.services.ai_service.settings.openai_api_key", None)
def test_plan_chatbot_query_requires_openai_api_key():
    with pytest.raises(
        RuntimeError,
        match="OpenAI API key is not configured",
    ):
        plan_chatbot_query(
            question="How many quizzes have I taken?",
            current_date="2026-08-25",
        )


def test_plan_chatbot_query_rejects_empty_question():
    with patch(
        "app.services.ai_service.settings.openai_api_key",
        "test-key",
    ):
        with pytest.raises(
            ValueError,
            match="Chatbot question cannot be empty",
        ):
            plan_chatbot_query(
                question="   ",
                current_date="2026-08-25",
            )


def test_chatbot_query_plan_rejects_duplicate_metrics():
    with pytest.raises(
        ValidationError,
        match="Chatbot query metrics must be unique",
    ):
        ChatbotQueryPlan(
            metrics=[
                "attempt_count",
                "attempt_count",
            ],
        )


def test_chatbot_query_plan_rejects_sort_metric_not_requested():
    with pytest.raises(
        ValidationError,
        match="sort_by must be included in metrics",
    ):
        ChatbotQueryPlan(
            metrics=[
                "attempt_count",
            ],
            group_by="quiz",
            sort_by="average_score",
        )


def test_chatbot_query_plan_rejects_unsupported_metric():
    with pytest.raises(ValidationError):
        ChatbotQueryPlan(
            metrics=["user_password"],
        )


def test_chatbot_query_plan_rejects_unsupported_grouping():
    with pytest.raises(ValidationError):
        ChatbotQueryPlan(
            metrics=["attempt_count"],
            group_by="user",
        )


def test_chatbot_query_plan_enforces_safe_limit():
    with pytest.raises(ValidationError):
        ChatbotQueryPlan(
            metrics=["attempt_count"],
            group_by="quiz",
            limit=101,
        )

def test_plan_chatbot_query_returns_monthly_report_plan():
    parsed_result = ChatbotPlan(
        intent="monthly_report",
        monthly_report=ChatbotMonthlyReportPlan(
            period="last_month",
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question="Give me my report for last month.",
            current_date="2026-08-25",
        )

    assert result.intent == "monthly_report"
    assert result.query is None
    assert result.monthly_report is not None
    assert result.monthly_report.period == "last_month"


def test_chatbot_plan_requires_query_for_query_intent():
    with pytest.raises(
        ValidationError,
        match="Query intent requires a query plan",
    ):
        ChatbotPlan(
            intent="query",
        )


def test_chatbot_plan_requires_report_for_report_intent():
    with pytest.raises(
        ValidationError,
        match="Monthly report intent requires a report plan",
    ):
        ChatbotPlan(
            intent="monthly_report",
        )


def test_chatbot_plan_rejects_query_and_report_together():
    with pytest.raises(
        ValidationError,
        match="Query intent cannot include another intent plan",
    ):
        ChatbotPlan(
            intent="query",
            query=ChatbotQueryPlan(
                metrics=["attempt_count"],
            ),
            monthly_report=ChatbotMonthlyReportPlan(
                period="last_month",
            ),
        )

def test_plan_chatbot_query_returns_question_performance_plan():
    parsed_result = ChatbotPlan(
        intent="question_performance",
        question_performance=ChatbotQuestionPerformancePlan(
            quiz_title=None,
            limit=10,
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question="Which questions do I keep getting wrong?",
            current_date="2026-08-25",
        )

    assert result.intent == "question_performance"
    assert result.query is None
    assert result.monthly_report is None
    assert result.question_performance is not None
    assert result.question_performance.quiz_title is None
    assert result.question_performance.limit == 10


def test_question_performance_plan_supports_quiz_filter():
    plan = ChatbotPlan(
        intent="question_performance",
        question_performance=ChatbotQuestionPerformancePlan(
            quiz_title="Python Basics",
            limit=5,
        ),
    )

    assert plan.question_performance is not None
    assert plan.question_performance.quiz_title == "Python Basics"
    assert plan.question_performance.limit == 5


def test_question_performance_plan_enforces_safe_limit():
    with pytest.raises(ValidationError):
        ChatbotQuestionPerformancePlan(
            limit=51,
        )


def test_chatbot_plan_requires_question_performance_plan():
    with pytest.raises(
        ValidationError,
        match=(
            "Question performance intent requires "
            "a performance plan"
        ),
    ):
        ChatbotPlan(
            intent="question_performance",
        )



def test_performance_trend_plan_supports_quiz_filter():
    plan = ChatbotPlan(
        intent="performance_trend",
        performance_trend=ChatbotPerformanceTrendPlan(
            quiz_title="Python Basics",
        ),
    )

    assert plan.performance_trend is not None
    assert plan.performance_trend.quiz_title == "Python Basics"
    assert plan.performance_trend.category is None


def test_performance_trend_plan_supports_category_filter():
    plan = ChatbotPlan(
        intent="performance_trend",
        performance_trend=ChatbotPerformanceTrendPlan(
            category="Programming",
        ),
    )

    assert plan.performance_trend is not None
    assert plan.performance_trend.category == "Programming"


def test_chatbot_plan_requires_performance_trend_plan():
    with pytest.raises(
        ValidationError,
        match="Performance trend intent requires a trend plan",
    ):
        ChatbotPlan(
            intent="performance_trend",
        )


def test_attempt_comparison_plan_defaults_to_three():
    plan = ChatbotPlan(
        intent="attempt_comparison",
        attempt_comparison=ChatbotAttemptComparisonPlan(
            quiz_title="JavaScript Fundamentals",
        ),
    )

    assert plan.attempt_comparison is not None
    assert plan.attempt_comparison.quiz_title == (
        "JavaScript Fundamentals"
    )
    assert plan.attempt_comparison.limit == 3


def test_attempt_comparison_plan_supports_category():
    plan = ChatbotPlan(
        intent="attempt_comparison",
        attempt_comparison=ChatbotAttemptComparisonPlan(
            category="Programming",
            limit=5,
        ),
    )

    assert plan.attempt_comparison is not None
    assert plan.attempt_comparison.category == "Programming"
    assert plan.attempt_comparison.limit == 5


def test_attempt_comparison_plan_enforces_safe_limit():
    with pytest.raises(ValidationError):
        ChatbotAttemptComparisonPlan(
            limit=21,
        )


def test_chatbot_plan_requires_attempt_comparison_plan():
    with pytest.raises(
        ValidationError,
        match=(
            "Attempt comparison intent requires "
            "a comparison plan"
        ),
    ):
        ChatbotPlan(
            intent="attempt_comparison",
        )


def test_plan_chatbot_query_returns_performance_trend_plan():
    parsed_result = ChatbotPlan(
        intent="performance_trend",
        performance_trend=ChatbotPerformanceTrendPlan(
            quiz_title="Python Basics",
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question="Am I improving at Python Basics?",
            current_date="2026-08-25",
        )

    assert result.intent == "performance_trend"
    assert result.performance_trend is not None
    assert result.performance_trend.quiz_title == "Python Basics"
    assert result.performance_trend.category is None


def test_plan_chatbot_query_returns_attempt_comparison_plan():
    parsed_result = ChatbotPlan(
        intent="attempt_comparison",
        attempt_comparison=ChatbotAttemptComparisonPlan(
            quiz_title="JavaScript Fundamentals",
            limit=3,
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question=(
                "Compare my last 3 attempts on "
                "JavaScript Fundamentals."
            ),
            current_date="2026-08-25",
        )

    assert result.intent == "attempt_comparison"
    assert result.attempt_comparison is not None
    assert result.attempt_comparison.quiz_title == (
        "JavaScript Fundamentals"
    )
    assert result.attempt_comparison.limit == 3


def test_chatbot_plan_accepts_study_recommendation():
    from app.schemas.ai import (
        ChatbotPlan,
        ChatbotStudyRecommendationPlan,
    )

    plan = ChatbotPlan(
        intent="study_recommendation",
        study_recommendation=ChatbotStudyRecommendationPlan(
            quiz_title="JavaScript Fundamentals",
            limit=5,
        ),
    )

    assert plan.intent == "study_recommendation"
    assert plan.study_recommendation is not None
    assert (
        plan.study_recommendation.quiz_title
        == "JavaScript Fundamentals"
    )
    assert plan.study_recommendation.limit == 5


def test_study_recommendation_defaults_to_five():
    from app.schemas.ai import ChatbotStudyRecommendationPlan

    plan = ChatbotStudyRecommendationPlan()

    assert plan.quiz_title is None
    assert plan.limit == 5


def test_chatbot_plan_rejects_missing_study_recommendation():
    import pytest
    from pydantic import ValidationError

    from app.schemas.ai import ChatbotPlan

    with pytest.raises(
        ValidationError,
        match=(
            "Study recommendation intent requires "
            "a recommendation plan"
        ),
    ):
        ChatbotPlan(
            intent="study_recommendation",
        )


def test_chatbot_plan_rejects_study_recommendation_with_other_plan():
    import pytest
    from pydantic import ValidationError

    from app.schemas.ai import (
        ChatbotPlan,
        ChatbotQuestionPerformancePlan,
        ChatbotStudyRecommendationPlan,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "Study recommendation intent cannot include "
            "another intent plan"
        ),
    ):
        ChatbotPlan(
            intent="study_recommendation",
            study_recommendation=(
                ChatbotStudyRecommendationPlan()
            ),
            question_performance=(
                ChatbotQuestionPerformancePlan()
            ),
        )

def test_plan_chatbot_query_returns_study_recommendation_plan():
    parsed_result = ChatbotPlan(
        intent="study_recommendation",
        study_recommendation=ChatbotStudyRecommendationPlan(
            quiz_title="JavaScript Fundamentals",
            limit=5,
        ),
    )

    with patch("app.services.ai_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.parse.return_value.output_parsed = (
            parsed_result
        )

        result = plan_chatbot_query(
            question=(
                "What should I study for "
                "JavaScript Fundamentals?"
            ),
            current_date="2026-08-25",
        )

    assert result.intent == "study_recommendation"
    assert result.study_recommendation is not None
    assert result.study_recommendation.quiz_title == (
        "JavaScript Fundamentals"
    )
    assert result.study_recommendation.limit == 5
    assert result.question_performance is None



def test_plan_chatbot_query_singular_worst_quiz_returns_one(monkeypatch):
    parsed = ChatbotPlan(
        intent="query",
        query=ChatbotQueryPlan(
            metrics=["average_score"],
            group_by="quiz",
            sort_by="average_score",
            sort_direction="asc",
            limit=1,
        ),
    )

    fake_response = SimpleNamespace(
        output_parsed=parsed,
    )
    fake_client = MagicMock()
    fake_client.responses.parse.return_value = fake_response

    monkeypatch.setattr(
        "app.services.ai_service.OpenAI",
        lambda **kwargs: fake_client,
    )
    monkeypatch.setattr(
        "app.services.ai_service.settings.openai_api_key",
        "test-key",
    )

    result = plan_chatbot_query(
        question="What quiz am I doing the worst on?",
        current_date="2026-08-25",
    )

    assert result.intent == "query"
    assert result.query is not None
    assert result.query.metrics == ["average_score"]
    assert result.query.group_by == "quiz"
    assert result.query.sort_by == "average_score"
    assert result.query.sort_direction == "asc"
    assert result.query.limit == 1


def test_plan_chatbot_query_multiple_worst_quizzes_uses_requested_limit(
    monkeypatch,
):
    parsed = ChatbotPlan(
        intent="query",
        query=ChatbotQueryPlan(
            metrics=["average_score"],
            group_by="quiz",
            sort_by="average_score",
            sort_direction="asc",
            limit=3,
        ),
    )

    fake_response = SimpleNamespace(
        output_parsed=parsed,
    )
    fake_client = MagicMock()
    fake_client.responses.parse.return_value = fake_response

    monkeypatch.setattr(
        "app.services.ai_service.OpenAI",
        lambda **kwargs: fake_client,
    )
    monkeypatch.setattr(
        "app.services.ai_service.settings.openai_api_key",
        "test-key",
    )

    result = plan_chatbot_query(
        question="What are my 3 worst quizzes?",
        current_date="2026-08-25",
    )

    assert result.intent == "query"
    assert result.query is not None
    assert result.query.limit == 3
