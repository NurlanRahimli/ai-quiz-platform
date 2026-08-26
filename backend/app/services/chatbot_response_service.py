from app.schemas.chatbot import ChatbotQueryResponse
from app.services.chatbot_query_service import ChatbotQueryResult


METRIC_LABELS = {
    "attempt_count": "attempts",
    "quiz_count": "quizzes",
    "average_score": "average score",
}


def _format_number(
    metric: str,
    value: object,
) -> str:
    if value is None:
        return "No data"

    if metric == "average_score":
        if isinstance(value, (int, float)):
            return f"{value:g}%"

    return str(value)


def _single_metric_message(
    metric: str,
    value: object,
) -> str:
    formatted = _format_number(
        metric,
        value,
    )

    if value is None:
        if metric == "average_score":
            return "You don't have a graded average yet."

        return "No matching data was found."

    if metric == "quiz_count":
        noun = "quiz" if value == 1 else "quizzes"
        return f"You've taken {formatted} {noun}."

    if metric == "created_quiz_count":
        if value == 0:
            return "You haven't created any quizzes yet."

        noun = "quiz" if value == 1 else "quizzes"
        return f"You've created {formatted} {noun}."

    if metric == "follower_count":
        if value == 0:
            return "You don't have any followers yet."

        noun = "follower" if value == 1 else "followers"
        return f"You have {formatted} {noun}."

    if metric == "following_count":
        if value == 0:
            return "You're not following anyone yet."

        noun = "person" if value == 1 else "people"
        return f"You're following {formatted} {noun}."

    if metric == "attempt_count":
        noun = "attempt" if value == 1 else "attempts"
        return f"You've made {formatted} {noun}."

    if metric == "average_score":
        return f"Your average score is {formatted}."

    return formatted


def _format_score(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:g}%"

    return str(value)


def _performance_trend_message(
    row: dict[str, object],
) -> str:
    quiz_title = str(row["quiz_title"])
    attempt_count = int(row["attempt_count"])
    first_score = _format_score(row["first_score"])
    latest_score = _format_score(row["latest_score"])
    direction = row["direction"]

    if direction == "improving":
        score_change = abs(float(row["score_change"]))
        return (
            f"Yes — you're improving on {quiz_title}. "
            f"Your score increased from {first_score} to "
            f"{latest_score}, a {score_change:g}-point "
            f"improvement across {attempt_count} attempts."
        )

    if direction == "declining":
        score_change = abs(float(row["score_change"]))
        return (
            f"Your recent performance on {quiz_title} has declined. "
            f"Your score went from {first_score} to "
            f"{latest_score}, a {score_change:g}-point "
            f"decrease across {attempt_count} attempts."
        )

    if direction == "stable":
        return (
            f"Your performance on {quiz_title} has stayed stable "
            f"at {latest_score} across {attempt_count} attempts."
        )

    if direction == "insufficient_data":
        return (
            f"You've scored {latest_score} on {quiz_title} so far. "
            "Take it again and I'll be able to show you "
            "a performance trend."
        )

    return "No matching performance trend was found."


def _is_study_recommendation_result(
    result: ChatbotQueryResult,
) -> bool:
    required_columns = {
        "priority",
        "question_text",
        "wrong_count",
        "miss_rate",
        "reason",
    }
    return required_columns.issubset(
        set(result.columns)
    )


def format_chatbot_query_result(
    result: ChatbotQueryResult,
) -> ChatbotQueryResponse:
    if _is_study_recommendation_result(result):
        if not result.rows:
            return ChatbotQueryResponse(
                type="text",
                message=(
                    "I don't have enough missed-question data "
                    "to recommend what to study yet."
                ),
            )

        if result.total_rows == 1:
            message = (
                "Based on your performance, here's the "
                "question I'd focus on next."
            )
        else:
            message = (
                "Based on your performance, here are the "
                f"{result.total_rows} questions I'd focus "
                "on next."
            )

        return ChatbotQueryResponse(
            type="table",
            message=message,
            columns=result.columns,
            rows=result.rows,
            total_rows=result.total_rows,
        )

    if (
        result.total_rows == 1
        and len(result.columns) == 1
        and len(result.rows) == 1
    ):
        metric = result.columns[0]
        value = result.rows[0].get(metric)

        return ChatbotQueryResponse(
            type="text",
            message=_single_metric_message(
                metric,
                value,
            ),
        )

    is_user_connection_list = {
        "user_id",
        "display_name",
    }.issubset(result.columns)

    if not result.rows:
        if is_user_connection_list:
            return ChatbotQueryResponse(
                type="text",
                message=(
                    "There aren't any users to show for "
                    "this connection list yet."
                ),
            )

        return ChatbotQueryResponse(
            type="text",
            message="No matching data was found.",
        )

    is_performance_trend = {
        "quiz_title",
        "attempt_count",
        "first_score",
        "latest_score",
        "score_change",
        "direction",
    }.issubset(result.columns)

    if (
        is_performance_trend
        and result.total_rows == 1
        and len(result.rows) == 1
    ):
        return ChatbotQueryResponse(
            type="text",
            message=_performance_trend_message(
                result.rows[0]
            ),
        )

    is_question_performance = {
        "question_id",
        "question_text",
        "wrong_count",
        "miss_rate",
    }.issubset(result.columns)

    is_attempt_comparison = {
        "attempt_id",
        "quiz_id",
        "quiz_title",
        "submitted_at",
        "score_percentage",
    }.issubset(result.columns)

    if is_user_connection_list:
        noun = (
            "person"
            if result.total_rows == 1
            else "people"
        )
        message = (
            f"Here {'is' if result.total_rows == 1 else 'are'} "
            f"{result.total_rows} {noun}."
        )
    elif is_question_performance:
        noun = (
            "question"
            if result.total_rows == 1
            else "questions"
        )
        message = (
            f"I found {result.total_rows} {noun} "
            "you've been missing most often."
        )
    elif is_attempt_comparison:
        noun = (
            "attempt"
            if result.total_rows == 1
            else "attempts"
        )
        message = (
            f"Here are your {result.total_rows} most recent "
            f"graded {noun}."
        )
    else:
        message = (
            f"I found {result.total_rows} "
            f"{'result' if result.total_rows == 1 else 'results'}."
        )

    return ChatbotQueryResponse(
        type="table",
        message=message,
        columns=result.columns,
        rows=result.rows,
        total_rows=result.total_rows,
    )
