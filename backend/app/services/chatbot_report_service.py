from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.chatbot_data_service import ChatbotAttemptRow


@dataclass(frozen=True)
class ChatbotCategoryReport:
    category: str
    attempt_count: int
    average_score: float | None


@dataclass(frozen=True)
class ChatbotMonthlyReport:
    year: int
    month: int
    attempt_count: int
    quiz_count: int
    average_score: float | None
    previous_attempt_count: int
    previous_quiz_count: int
    previous_average_score: float | None
    attempt_change: int
    quiz_change: int
    score_change: float | None
    strongest_category: ChatbotCategoryReport | None
    weakest_category: ChatbotCategoryReport | None


def _month_bounds(
    year: int,
    month: int,
) -> tuple[datetime, datetime]:
    start = datetime(
        year,
        month,
        1,
        tzinfo=timezone.utc,
    )

    if month == 12:
        end = datetime(
            year + 1,
            1,
            1,
            tzinfo=timezone.utc,
        )
    else:
        end = datetime(
            year,
            month + 1,
            1,
            tzinfo=timezone.utc,
        )

    return start, end


def _previous_month(
    year: int,
    month: int,
) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12

    return year, month - 1


def _rows_for_month(
    rows: list[ChatbotAttemptRow],
    *,
    year: int,
    month: int,
) -> list[ChatbotAttemptRow]:
    start, end = _month_bounds(
        year,
        month,
    )

    return [
        row
        for row in rows
        if start <= row.submitted_at < end
    ]


def _average_score(
    rows: list[ChatbotAttemptRow],
) -> float | None:
    scores = [
        row.score_percentage
        for row in rows
        if row.score_percentage is not None
    ]

    if not scores:
        return None

    return round(
        sum(scores) / len(scores),
        2,
    )


def _category_reports(
    rows: list[ChatbotAttemptRow],
) -> list[ChatbotCategoryReport]:
    grouped: dict[
        str,
        list[ChatbotAttemptRow],
    ] = {}

    for row in rows:
        category = row.category or "Uncategorized"

        grouped.setdefault(
            category,
            [],
        ).append(row)

    reports: list[ChatbotCategoryReport] = []

    for category, category_rows in grouped.items():
        reports.append(
            ChatbotCategoryReport(
                category=category,
                attempt_count=len(category_rows),
                average_score=_average_score(
                    category_rows
                ),
            )
        )

    return reports


def build_monthly_report(
    rows: list[ChatbotAttemptRow],
    *,
    year: int,
    month: int,
) -> ChatbotMonthlyReport:
    current_rows = _rows_for_month(
        rows,
        year=year,
        month=month,
    )

    previous_year, previous_month = _previous_month(
        year,
        month,
    )

    previous_rows = _rows_for_month(
        rows,
        year=previous_year,
        month=previous_month,
    )

    current_average = _average_score(
        current_rows
    )
    previous_average = _average_score(
        previous_rows
    )

    current_quiz_count = len({
        row.quiz_id
        for row in current_rows
    })

    previous_quiz_count = len({
        row.quiz_id
        for row in previous_rows
    })

    category_reports = [
        report
        for report in _category_reports(current_rows)
        if (
            report.average_score is not None
            and report.category != "Uncategorized"
        )
    ]

    strongest_category = (
        max(
            category_reports,
            key=lambda report: (
                report.average_score,
                report.attempt_count,
            ),
        )
        if category_reports
        else None
    )

    weakest_category = (
        min(
            category_reports,
            key=lambda report: (
                report.average_score,
                -report.attempt_count,
            ),
        )
        if category_reports
        else None
    )

    score_change = (
        round(
            current_average - previous_average,
            2,
        )
        if (
            current_average is not None
            and previous_average is not None
        )
        else None
    )

    return ChatbotMonthlyReport(
        year=year,
        month=month,
        attempt_count=len(current_rows),
        quiz_count=current_quiz_count,
        average_score=current_average,
        previous_attempt_count=len(previous_rows),
        previous_quiz_count=previous_quiz_count,
        previous_average_score=previous_average,
        attempt_change=(
            len(current_rows) - len(previous_rows)
        ),
        quiz_change=(
            current_quiz_count
            - previous_quiz_count
        ),
        score_change=score_change,
        strongest_category=strongest_category,
        weakest_category=weakest_category,
    )
