from dataclasses import dataclass

from app.services.chatbot_data_service import (
    ChatbotQuestionPerformanceRow,
)


@dataclass(frozen=True)
class ChatbotQuestionPerformanceSummary:
    quiz_id: str
    quiz_title: str
    question_id: str
    question_text: str
    attempt_count: int
    correct_count: int
    wrong_count: int
    miss_rate: float


def summarize_question_performance(
    rows: list[ChatbotQuestionPerformanceRow],
    *,
    quiz_title: str | None = None,
    wrong_only: bool = False,
    limit: int = 20,
) -> list[ChatbotQuestionPerformanceSummary]:
    filtered_rows = rows

    if quiz_title is not None:
        normalized_title = quiz_title.strip().lower()
        filtered_rows = [
            row
            for row in filtered_rows
            if normalized_title in row.quiz_title.lower()
        ]

    grouped: dict[
        tuple[str, str],
        list[ChatbotQuestionPerformanceRow],
    ] = {}

    for row in filtered_rows:
        key = (
            str(row.quiz_id),
            str(row.question_id),
        )
        grouped.setdefault(key, []).append(row)

    summaries: list[ChatbotQuestionPerformanceSummary] = []

    for question_rows in grouped.values():
        first = question_rows[0]
        attempt_count = len(question_rows)
        correct_count = sum(
            1
            for row in question_rows
            if row.is_correct
        )
        wrong_count = attempt_count - correct_count

        if wrong_only and wrong_count == 0:
            continue

        miss_rate = round(
            (wrong_count / attempt_count) * 100,
            2,
        )

        summaries.append(
            ChatbotQuestionPerformanceSummary(
                quiz_id=str(first.quiz_id),
                quiz_title=first.quiz_title,
                question_id=str(first.question_id),
                question_text=first.question_text,
                attempt_count=attempt_count,
                correct_count=correct_count,
                wrong_count=wrong_count,
                miss_rate=miss_rate,
            )
        )

    summaries.sort(
        key=lambda summary: (
            summary.wrong_count,
            summary.miss_rate,
            summary.attempt_count,
        ),
        reverse=True,
    )

    safe_limit = min(
        max(limit, 1),
        100,
    )

    return summaries[:safe_limit]
