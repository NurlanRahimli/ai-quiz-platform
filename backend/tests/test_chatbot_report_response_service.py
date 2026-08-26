from app.services.chatbot_report_service import (
    ChatbotCategoryReport,
    ChatbotMonthlyReport,
)
from app.services.chatbot_report_response_service import (
    format_monthly_report,
)


def make_report(**overrides):
    values = {
        "year": 2026,
        "month": 8,
        "attempt_count": 10,
        "quiz_count": 3,
        "average_score": 82.5,
        "previous_attempt_count": 7,
        "previous_quiz_count": 2,
        "previous_average_score": 75.0,
        "attempt_change": 3,
        "quiz_change": 1,
        "score_change": 7.5,
        "strongest_category": ChatbotCategoryReport(
            category="Mathematics",
            attempt_count=4,
            average_score=92.0,
        ),
        "weakest_category": ChatbotCategoryReport(
            category="Programming",
            attempt_count=3,
            average_score=52.0,
        ),
    }

    values.update(overrides)

    return ChatbotMonthlyReport(**values)


def test_formats_monthly_report():
    response = format_monthly_report(
        make_report()
    )

    assert response.type == "report"
    assert response.title == (
        "August 2026 Performance Report"
    )
    assert len(response.insights) == 5

    average = response.insights[0]

    assert average.status == "positive"
    assert average.icon == "chart-no-axes-combined"
    assert average.label == "Average Score"
    assert average.value == "82.5%"
    assert average.detail == (
        "Up 7.5 points from the previous month."
    )


def test_report_marks_middle_score_as_warning():
    response = format_monthly_report(
        make_report(
            average_score=72.0,
            score_change=-3.0,
        )
    )

    average = response.insights[0]

    assert average.status == "warning"
    assert average.value == "72%"
    assert average.detail == (
        "Down 3 points from the previous month."
    )


def test_report_marks_low_score_as_negative():
    response = format_monthly_report(
        make_report(
            average_score=48.5,
        )
    )

    assert response.insights[0].status == "negative"


def test_report_formats_attempt_decrease():
    response = format_monthly_report(
        make_report(
            attempt_count=4,
            previous_attempt_count=7,
            attempt_change=-3,
        )
    )

    attempts = response.insights[1]

    assert attempts.status == "negative"
    assert attempts.detail == (
        "3 fewer attempts than the previous month."
    )


def test_report_handles_no_previous_score():
    response = format_monthly_report(
        make_report(
            previous_average_score=None,
            score_change=None,
        )
    )

    assert response.insights[0].detail == (
        "No previous graded average to compare."
    )


def test_report_does_not_duplicate_single_category():
    category = ChatbotCategoryReport(
        category="Science",
        attempt_count=4,
        average_score=85.0,
    )

    response = format_monthly_report(
        make_report(
            strongest_category=category,
            weakest_category=category,
        )
    )

    labels = [
        insight.label
        for insight in response.insights
    ]

    assert "Strongest Category" in labels
    assert "Needs Attention" not in labels


def test_report_handles_no_attempts():
    response = format_monthly_report(
        make_report(
            attempt_count=0,
            quiz_count=0,
            average_score=None,
            previous_attempt_count=0,
            previous_quiz_count=0,
            previous_average_score=None,
            attempt_change=0,
            quiz_change=0,
            score_change=None,
            strongest_category=None,
            weakest_category=None,
        )
    )

    assert response.type == "report"
    assert response.insights == []
    assert response.message == (
        "You didn't complete any quizzes during this period."
    )
