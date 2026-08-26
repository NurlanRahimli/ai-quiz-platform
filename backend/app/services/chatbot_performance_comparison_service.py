from dataclasses import dataclass
from typing import Literal

from app.services.chatbot_data_service import ChatbotAttemptRow


TrendDirection = Literal[
    "improving",
    "declining",
    "stable",
    "insufficient_data",
]


@dataclass(frozen=True)
class ChatbotAttemptComparison:
    attempt_id: str
    quiz_id: str
    quiz_title: str
    submitted_at: str
    score_percentage: float


@dataclass(frozen=True)
class ChatbotPerformanceTrend:
    quiz_id: str
    quiz_title: str
    attempt_count: int
    first_score: float | None
    latest_score: float | None
    score_change: float | None
    direction: TrendDirection


def _matching_graded_attempts(
    rows: list[ChatbotAttemptRow],
    *,
    quiz_title: str | None = None,
    category: str | None = None,
) -> list[ChatbotAttemptRow]:
    matching = [
        row
        for row in rows
        if row.score_percentage is not None
    ]

    if quiz_title is not None:
        normalized_title = quiz_title.strip().lower()
        matching = [
            row
            for row in matching
            if normalized_title in row.quiz_title.lower()
        ]

    if category is not None:
        normalized_category = category.strip().lower()
        matching = [
            row
            for row in matching
            if (
                row.category is not None
                and row.category.lower() == normalized_category
            )
        ]

    return matching


def compare_recent_attempts(
    rows: list[ChatbotAttemptRow],
    *,
    quiz_title: str | None = None,
    category: str | None = None,
    limit: int = 3,
) -> list[ChatbotAttemptComparison]:
    matching = _matching_graded_attempts(
        rows,
        quiz_title=quiz_title,
        category=category,
    )

    matching.sort(
        key=lambda row: (
            row.submitted_at,
            str(row.attempt_id),
        ),
        reverse=True,
    )

    safe_limit = min(max(limit, 1), 20)

    return [
        ChatbotAttemptComparison(
            attempt_id=str(row.attempt_id),
            quiz_id=str(row.quiz_id),
            quiz_title=row.quiz_title,
            submitted_at=row.submitted_at.isoformat(),
            score_percentage=row.score_percentage,
        )
        for row in matching[:safe_limit]
        if row.score_percentage is not None
    ]


def calculate_performance_trend(
    rows: list[ChatbotAttemptRow],
    *,
    quiz_title: str | None = None,
    category: str | None = None,
) -> ChatbotPerformanceTrend | None:
    matching = _matching_graded_attempts(
        rows,
        quiz_title=quiz_title,
        category=category,
    )

    if not matching:
        return None

    matching.sort(
        key=lambda row: (
            row.submitted_at,
            str(row.attempt_id),
        )
    )

    first = matching[0]
    latest = matching[-1]

    if len(matching) < 2:
        return ChatbotPerformanceTrend(
            quiz_id=str(latest.quiz_id),
            quiz_title=latest.quiz_title,
            attempt_count=1,
            first_score=latest.score_percentage,
            latest_score=latest.score_percentage,
            score_change=None,
            direction="insufficient_data",
        )

    first_score = first.score_percentage
    latest_score = latest.score_percentage

    if first_score is None or latest_score is None:
        raise RuntimeError(
            "Trend calculation received an ungraded attempt"
        )

    change = round(latest_score - first_score, 2)

    if change > 0:
        direction: TrendDirection = "improving"
    elif change < 0:
        direction = "declining"
    else:
        direction = "stable"

    return ChatbotPerformanceTrend(
        quiz_id=str(latest.quiz_id),
        quiz_title=latest.quiz_title,
        attempt_count=len(matching),
        first_score=first_score,
        latest_score=latest_score,
        score_change=change,
        direction=direction,
    )
