import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.schemas.ai import (
    ChatbotPlan,
    ChatbotQueryPlan,
)
from app.schemas.chatbot import ChatbotReportResponse
from app.services.ai_service import plan_chatbot_query
from app.services.chatbot_data_service import (
    get_user_attempt_rows,
    get_user_question_performance_rows,
)
from app.services.chatbot_created_quizzes_service import (
    count_user_created_quizzes,
    list_user_created_quizzes,
)
from app.services.chatbot_user_connections_service import (
    count_user_connections,
    list_user_connections,
)
from app.services.chatbot_question_performance_service import (
    summarize_question_performance,
)
from app.services.chatbot_study_recommendation_service import (
    build_study_recommendations,
)
from app.services.chatbot_report_response_service import (
    format_monthly_report,
)
from app.services.chatbot_report_service import (
    build_monthly_report,
)
from app.services.chatbot_performance_comparison_service import (
    calculate_performance_trend,
    compare_recent_attempts,
)

from app.services.chatbot_query_service import (
    ChatbotQuery,
    ChatbotQueryFilters,
    ChatbotQueryResult,
    execute_chatbot_query,
)


def _parse_optional_datetime(
    value: str | None,
) -> datetime | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Invalid chatbot query datetime: {value}"
        ) from exc


def _query_from_plan(
    plan: ChatbotQueryPlan,
) -> ChatbotQuery:
    return ChatbotQuery(
        metrics=tuple(plan.metrics),
        group_by=plan.group_by,
        filters=ChatbotQueryFilters(
            quiz_title=plan.filters.quiz_title,
            category=plan.filters.category,
            creator_name=plan.filters.creator_name,
            date_from=_parse_optional_datetime(
                plan.filters.date_from
            ),
            date_to=_parse_optional_datetime(
                plan.filters.date_to
            ),
        ),
        sort_by=plan.sort_by,
        sort_direction=plan.sort_direction,
        limit=plan.limit,
    )




def _resolve_report_month(
    *,
    current_date: str,
    period: str,
) -> tuple[int, int]:
    parsed_date = date.fromisoformat(current_date)

    if period == "this_month":
        return parsed_date.year, parsed_date.month

    if period == "last_month":
        if parsed_date.month == 1:
            return parsed_date.year - 1, 12

        return parsed_date.year, parsed_date.month - 1

    raise ValueError(
        f"Unsupported chatbot report period: {period}"
    )

def answer_chatbot_data_question(
    db: Session,
    *,
    user_id: uuid.UUID,
    question: str,
    current_date: str,
) -> ChatbotQueryResult | ChatbotReportResponse:
    plan = plan_chatbot_query(
        question=question,
        current_date=current_date,
    )

    if plan.intent == "user_connections":
        if plan.user_connections is None:
            raise RuntimeError(
                "Chatbot user connections plan is missing"
            )

        direction = plan.user_connections.direction
        operation = plan.user_connections.operation

        if operation == "count":
            connection_count = count_user_connections(
                db,
                user_id=user_id,
                direction=direction,
            )

            count_column = (
                "follower_count"
                if direction == "followers"
                else "following_count"
            )

            return ChatbotQueryResult(
                columns=[count_column],
                rows=[
                    {
                        count_column: connection_count,
                    }
                ],
                total_rows=1,
            )

        if operation == "list":
            users = list_user_connections(
                db,
                user_id=user_id,
                direction=direction,
                limit=plan.user_connections.limit,
            )

            return ChatbotQueryResult(
                columns=[
                    "user_id",
                    "display_name",
                ],
                rows=[
                    {
                        "user_id": str(user.id),
                        "display_name": user.display_name,
                    }
                    for user in users
                ],
                total_rows=len(users),
            )

        raise RuntimeError(
            "Unsupported user connections operation: "
            f"{operation}"
        )

    if plan.intent == "created_quizzes":
        if plan.created_quizzes is None:
            raise RuntimeError(
                "Chatbot created quizzes plan is missing"
            )

        if plan.created_quizzes.operation == "count":
            created_quiz_count = count_user_created_quizzes(
                db,
                user_id=user_id,
                visibility=plan.created_quizzes.visibility,
                category=plan.created_quizzes.category,
                title_search=plan.created_quizzes.title_search,
            )

            return ChatbotQueryResult(
                columns=["created_quiz_count"],
                rows=[
                    {
                        "created_quiz_count": created_quiz_count,
                    }
                ],
                total_rows=1,
            )

        if plan.created_quizzes.operation == "list":
            quizzes = list_user_created_quizzes(
                db,
                user_id=user_id,
                visibility=plan.created_quizzes.visibility,
                category=plan.created_quizzes.category,
                title_search=plan.created_quizzes.title_search,
                sort_direction=plan.created_quizzes.sort_direction,
                limit=plan.created_quizzes.limit,
            )

            return ChatbotQueryResult(
                columns=[
                    "quiz_id",
                    "quiz_title",
                    "category",
                    "visibility",
                    "created_at",
                ],
                rows=[
                    {
                        "quiz_id": str(quiz.id),
                        "quiz_title": quiz.title,
                        "category": quiz.category,
                        "visibility": quiz.visibility,
                        "created_at": quiz.created_at.isoformat(),
                    }
                    for quiz in quizzes
                ],
                total_rows=len(quizzes),
            )

        raise RuntimeError(
            "Unsupported created quizzes operation: "
            f"{plan.created_quizzes.operation}"
        )

    if plan.intent == "question_performance":
        if plan.question_performance is None:
            raise RuntimeError(
                "Chatbot question performance plan is missing"
            )

        question_rows = get_user_question_performance_rows(
            db,
            user_id=user_id,
        )

        summaries = summarize_question_performance(
            question_rows,
            quiz_title=plan.question_performance.quiz_title,
            wrong_only=True,
            limit=plan.question_performance.limit,
        )

        return ChatbotQueryResult(
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
                    "quiz_id": summary.quiz_id,
                    "quiz_title": summary.quiz_title,
                    "question_id": summary.question_id,
                    "question_text": summary.question_text,
                    "attempt_count": summary.attempt_count,
                    "correct_count": summary.correct_count,
                    "wrong_count": summary.wrong_count,
                    "miss_rate": summary.miss_rate,
                }
                for summary in summaries
            ],
            total_rows=len(summaries),
        )

    if plan.intent == "study_recommendation":
        if plan.study_recommendation is None:
            raise RuntimeError(
                "Chatbot study recommendation plan is missing"
            )

        question_rows = get_user_question_performance_rows(
            db,
            user_id=user_id,
        )

        recommendations = build_study_recommendations(
            question_rows,
            quiz_title=plan.study_recommendation.quiz_title,
            limit=plan.study_recommendation.limit,
        )

        return ChatbotQueryResult(
            columns=[
                "priority",
                "quiz_id",
                "quiz_title",
                "question_id",
                "question_text",
                "attempt_count",
                "wrong_count",
                "miss_rate",
                "reason",
            ],
            rows=[
                {
                    "priority": recommendation.priority,
                    "quiz_id": recommendation.quiz_id,
                    "quiz_title": recommendation.quiz_title,
                    "question_id": recommendation.question_id,
                    "question_text": recommendation.question_text,
                    "attempt_count": recommendation.attempt_count,
                    "wrong_count": recommendation.wrong_count,
                    "miss_rate": recommendation.miss_rate,
                    "reason": recommendation.reason,
                }
                for recommendation in recommendations
            ],
            total_rows=len(recommendations),
        )

    rows = get_user_attempt_rows(
        db,
        user_id=user_id,
    )

    if plan.intent == "performance_trend":
        if plan.performance_trend is None:
            raise RuntimeError(
                "Chatbot performance trend plan is missing"
            )

        trend = calculate_performance_trend(
            rows,
            quiz_title=plan.performance_trend.quiz_title,
            category=plan.performance_trend.category,
        )

        if trend is None:
            return ChatbotQueryResult(
                columns=[],
                rows=[],
                total_rows=0,
            )

        return ChatbotQueryResult(
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
                    "quiz_id": trend.quiz_id,
                    "quiz_title": trend.quiz_title,
                    "attempt_count": trend.attempt_count,
                    "first_score": trend.first_score,
                    "latest_score": trend.latest_score,
                    "score_change": trend.score_change,
                    "direction": trend.direction,
                }
            ],
            total_rows=1,
        )

    if plan.intent == "attempt_comparison":
        if plan.attempt_comparison is None:
            raise RuntimeError(
                "Chatbot attempt comparison plan is missing"
            )

        comparisons = compare_recent_attempts(
            rows,
            quiz_title=plan.attempt_comparison.quiz_title,
            category=plan.attempt_comparison.category,
            limit=plan.attempt_comparison.limit,
        )

        return ChatbotQueryResult(
            columns=[
                "attempt_id",
                "quiz_id",
                "quiz_title",
                "submitted_at",
                "score_percentage",
            ],
            rows=[
                {
                    "attempt_id": comparison.attempt_id,
                    "quiz_id": comparison.quiz_id,
                    "quiz_title": comparison.quiz_title,
                    "submitted_at": comparison.submitted_at,
                    "score_percentage": comparison.score_percentage,
                }
                for comparison in comparisons
            ],
            total_rows=len(comparisons),
        )

    if plan.intent == "query":
        if plan.query is None:
            raise RuntimeError(
                "Chatbot query plan is missing"
            )

        query = _query_from_plan(
            plan.query
        )

        return execute_chatbot_query(
            rows,
            query,
        )

    if plan.intent == "monthly_report":
        if plan.monthly_report is None:
            raise RuntimeError(
                "Chatbot monthly report plan is missing"
            )

        year, month = _resolve_report_month(
            current_date=current_date,
            period=plan.monthly_report.period,
        )

        report = build_monthly_report(
            rows,
            year=year,
            month=month,
        )

        return format_monthly_report(
            report
        )

    raise RuntimeError(
        f"Unsupported chatbot intent: {plan.intent}"
    )

