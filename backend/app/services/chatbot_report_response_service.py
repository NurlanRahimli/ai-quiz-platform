import calendar

from app.schemas.chatbot import (
    ChatbotReportInsight,
    ChatbotReportResponse,
)
from app.services.chatbot_report_service import (
    ChatbotMonthlyReport,
)


def _score_status(
    score: float | None,
) -> str:
    if score is None:
        return "neutral"

    if score >= 80:
        return "positive"

    if score >= 60:
        return "warning"

    return "negative"


def _change_status(
    change: float | int | None,
) -> str:
    if change is None or change == 0:
        return "neutral"

    if change > 0:
        return "positive"

    return "negative"


def _score_value(
    score: float | None,
) -> str:
    if score is None:
        return "No graded score"

    return f"{score:g}%"


def _score_change_detail(
    report: ChatbotMonthlyReport,
) -> str:
    if report.score_change is None:
        return "No previous graded average to compare."

    if report.score_change > 0:
        return (
            f"Up {report.score_change:g} points "
            "from the previous month."
        )

    if report.score_change < 0:
        return (
            f"Down {abs(report.score_change):g} points "
            "from the previous month."
        )

    return "Unchanged from the previous month."


def _attempt_change_detail(
    report: ChatbotMonthlyReport,
) -> str:
    change = report.attempt_change

    if change > 0:
        return (
            f"{change} more "
            f"{'attempt' if change == 1 else 'attempts'} "
            "than the previous month."
        )

    if change < 0:
        difference = abs(change)
        return (
            f"{difference} fewer "
            f"{'attempt' if difference == 1 else 'attempts'} "
            "than the previous month."
        )

    return "Same number of attempts as the previous month."


def format_monthly_report(
    report: ChatbotMonthlyReport,
) -> ChatbotReportResponse:
    month_name = calendar.month_name[report.month]

    if report.attempt_count == 0:
        return ChatbotReportResponse(
            title=f"{month_name} {report.year} Performance Report",
            message=(
                "You didn't complete any quizzes during this period."
            ),
            insights=[],
        )

    insights: list[ChatbotReportInsight] = [
        ChatbotReportInsight(
            status=_score_status(report.average_score),
            icon="chart-no-axes-combined",
            label="Average Score",
            value=_score_value(report.average_score),
            detail=_score_change_detail(report),
        ),
        ChatbotReportInsight(
            status=_change_status(report.attempt_change),
            icon="activity",
            label="Quiz Attempts",
            value=str(report.attempt_count),
            detail=_attempt_change_detail(report),
        ),
        ChatbotReportInsight(
            status="neutral",
            icon="library-big",
            label="Quizzes Taken",
            value=str(report.quiz_count),
            detail=(
                f"{report.quiz_count} unique "
                f"{'quiz' if report.quiz_count == 1 else 'quizzes'} "
                "during this period."
            ),
        ),
    ]

    if report.strongest_category is not None:
        insights.append(
            ChatbotReportInsight(
                status="positive",
                icon="trophy",
                label="Strongest Category",
                value=report.strongest_category.category,
                detail=(
                    f"{_score_value(report.strongest_category.average_score)} "
                    "average score."
                ),
            )
        )

    if (
        report.weakest_category is not None
        and (
            report.strongest_category is None
            or report.weakest_category.category
            != report.strongest_category.category
        )
    ):
        insights.append(
            ChatbotReportInsight(
                status=_score_status(
                    report.weakest_category.average_score
                ),
                icon="triangle-alert",
                label="Needs Attention",
                value=report.weakest_category.category,
                detail=(
                    f"{_score_value(report.weakest_category.average_score)} "
                    "average score."
                ),
            )
        )

    return ChatbotReportResponse(
        title=f"{month_name} {report.year} Performance Report",
        message=(
            "Here's a summary of your quiz performance "
            "for this period."
        ),
        insights=insights,
    )
