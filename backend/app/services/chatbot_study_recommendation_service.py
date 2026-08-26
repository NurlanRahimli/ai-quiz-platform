from dataclasses import dataclass

from app.services.chatbot_data_service import (
    ChatbotQuestionPerformanceRow,
)
from app.services.chatbot_question_performance_service import (
    summarize_question_performance,
)


@dataclass(frozen=True)
class ChatbotStudyRecommendation:
    priority: int
    quiz_id: str
    quiz_title: str
    question_id: str
    question_text: str
    attempt_count: int
    wrong_count: int
    miss_rate: float
    reason: str


def build_study_recommendations(
    rows: list[ChatbotQuestionPerformanceRow],
    *,
    quiz_title: str | None = None,
    limit: int = 5,
) -> list[ChatbotStudyRecommendation]:
    safe_limit = min(
        max(limit, 1),
        10,
    )

    summaries = summarize_question_performance(
        rows,
        quiz_title=quiz_title,
        wrong_only=True,
        limit=safe_limit,
    )

    recommendations: list[
        ChatbotStudyRecommendation
    ] = []

    for index, summary in enumerate(
        summaries,
        start=1,
    ):
        wrong_noun = (
            "time"
            if summary.wrong_count == 1
            else "times"
        )

        reason = (
            f"You missed this question "
            f"{summary.wrong_count} {wrong_noun} "
            f"across {summary.attempt_count} "
            f"{'attempt' if summary.attempt_count == 1 else 'attempts'} "
            f"({summary.miss_rate:g}% miss rate)."
        )

        recommendations.append(
            ChatbotStudyRecommendation(
                priority=index,
                quiz_id=summary.quiz_id,
                quiz_title=summary.quiz_title,
                question_id=summary.question_id,
                question_text=summary.question_text,
                attempt_count=summary.attempt_count,
                wrong_count=summary.wrong_count,
                miss_rate=summary.miss_rate,
                reason=reason,
            )
        )

    return recommendations
