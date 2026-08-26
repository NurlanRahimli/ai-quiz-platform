from app.services.chatbot_query_service import ChatbotQueryResult
from app.services.chatbot_response_service import (
    format_chatbot_query_result,
)


def test_formats_quiz_count_as_text():
    result = ChatbotQueryResult(
        columns=["quiz_count"],
        rows=[{"quiz_count": 3}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You've taken 3 quizzes."
    assert response.columns == []
    assert response.rows == []
    assert response.total_rows == 0


def test_formats_attempt_count_as_text():
    result = ChatbotQueryResult(
        columns=["attempt_count"],
        rows=[{"attempt_count": 18}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You've made 18 attempts."


def test_formats_average_score_as_text():
    result = ChatbotQueryResult(
        columns=["average_score"],
        rows=[{"average_score": 62.5}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "Your average score is 62.5%."


def test_formats_grouped_results_as_table():
    result = ChatbotQueryResult(
        columns=[
            "quiz_title",
            "creator_name",
            "attempt_count",
            "average_score",
        ],
        rows=[
            {
                "quiz_title": "Python",
                "creator_name": "Alice",
                "attempt_count": 4,
                "average_score": 87.5,
            },
            {
                "quiz_title": "Biology",
                "creator_name": "Bob",
                "attempt_count": 2,
                "average_score": 75.0,
            },
        ],
        total_rows=2,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == "I found 2 results."
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.total_rows == 2


def test_formats_empty_grouped_result_as_text():
    result = ChatbotQueryResult(
        columns=["average_score"],
        rows=[],
        total_rows=0,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "No matching data was found."


def test_formats_missing_average_as_text():
    result = ChatbotQueryResult(
        columns=["average_score"],
        rows=[{"average_score": None}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You don't have a graded average yet."
    )

def test_formats_question_performance_results_with_specific_message():

    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-1",
                "question_text": "What is a Python list?",
                "attempt_count": 3,
                "correct_count": 1,
                "wrong_count": 2,
                "miss_rate": 66.67,
            },
            {
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-2",
                "question_text": "What does len() return?",
                "attempt_count": 2,
                "correct_count": 0,
                "wrong_count": 2,
                "miss_rate": 100.0,
            },
        ],
        total_rows=2,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == (
        "I found 2 questions you've been missing most often."
    )
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.total_rows == 2


def test_formats_single_question_performance_result_with_specific_message():

    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-1",
                "question_text": "What is a Python list?",
                "attempt_count": 3,
                "correct_count": 1,
                "wrong_count": 2,
                "miss_rate": 66.67,
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == (
        "I found 1 question you've been missing most often."
    )

def test_formats_improving_performance_trend_as_text():
    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "attempt_count": 4,
                "first_score": 25.0,
                "latest_score": 75.0,
                "score_change": 50.0,
                "direction": "improving",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "Yes — you're improving on JavaScript Fundamentals. "
        "Your score increased from 25% to 75%, "
        "a 50-point improvement across 4 attempts."
    )


def test_formats_declining_performance_trend_as_text():
    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "attempt_count": 3,
                "first_score": 90.0,
                "latest_score": 70.0,
                "score_change": -20.0,
                "direction": "declining",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "Your recent performance on Python Basics has declined. "
        "Your score went from 90% to 70%, "
        "a 20-point decrease across 3 attempts."
    )


def test_formats_stable_performance_trend_as_text():
    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "Biology",
                "attempt_count": 2,
                "first_score": 80.0,
                "latest_score": 80.0,
                "score_change": 0.0,
                "direction": "stable",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "Your performance on Biology has stayed stable at 80% "
        "across 2 attempts."
    )


def test_formats_insufficient_performance_trend_as_text():
    result = ChatbotQueryResult(
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
                "quiz_id": "quiz-1",
                "quiz_title": "Chemistry",
                "attempt_count": 1,
                "first_score": 85.0,
                "latest_score": 85.0,
                "score_change": None,
                "direction": "insufficient_data",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You've scored 85% on Chemistry so far. "
        "Take it again and I'll be able to show you a performance trend."
    )


def test_formats_attempt_comparison_with_specific_message():
    result = ChatbotQueryResult(
        columns=[
            "attempt_id",
            "quiz_id",
            "quiz_title",
            "submitted_at",
            "score_percentage",
        ],
        rows=[
            {
                "attempt_id": "attempt-3",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-25T12:00:00+00:00",
                "score_percentage": 75.0,
            },
            {
                "attempt_id": "attempt-2",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-24T12:00:00+00:00",
                "score_percentage": 50.0,
            },
            {
                "attempt_id": "attempt-1",
                "quiz_id": "quiz-1",
                "quiz_title": "JavaScript Fundamentals",
                "submitted_at": "2026-08-23T12:00:00+00:00",
                "score_percentage": 25.0,
            },
        ],
        total_rows=3,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == (
        "Here are your 3 most recent graded attempts."
    )
    assert response.rows == result.rows
    assert response.total_rows == 3

def test_formats_study_recommendations_with_specific_message():
    result = ChatbotQueryResult(
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
                "priority": 1,
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-1",
                "question_text": "What is a Python list?",
                "attempt_count": 4,
                "wrong_count": 3,
                "miss_rate": 75.0,
                "reason": "You missed this question 3 times.",
            },
            {
                "priority": 2,
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-2",
                "question_text": "What does len() return?",
                "attempt_count": 3,
                "wrong_count": 2,
                "miss_rate": 66.67,
                "reason": "You missed this question 2 times.",
            },
        ],
        total_rows=2,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == (
        "Based on your performance, here are the "
        "2 questions I'd focus on next."
    )
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.total_rows == 2


def test_formats_single_study_recommendation_with_specific_message():
    result = ChatbotQueryResult(
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
                "priority": 1,
                "quiz_id": "quiz-1",
                "quiz_title": "Python Basics",
                "question_id": "question-1",
                "question_text": "What is a Python list?",
                "attempt_count": 3,
                "wrong_count": 2,
                "miss_rate": 66.67,
                "reason": "You missed this question 2 times.",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == (
        "Based on your performance, here's the "
        "question I'd focus on next."
    )
    assert response.total_rows == 1


def test_formats_empty_study_recommendations_as_text():
    result = ChatbotQueryResult(
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
        rows=[],
        total_rows=0,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "I don't have enough missed-question data "
        "to recommend what to study yet."
    )



def test_formats_created_quiz_count_as_text():
    result = ChatbotQueryResult(
        columns=["created_quiz_count"],
        rows=[{"created_quiz_count": 8}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You've created 8 quizzes."
    assert response.columns == []
    assert response.rows == []
    assert response.total_rows == 0


def test_formats_single_created_quiz_count_as_text():
    result = ChatbotQueryResult(
        columns=["created_quiz_count"],
        rows=[{"created_quiz_count": 1}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You've created 1 quiz."


def test_formats_zero_created_quizzes_as_text():
    result = ChatbotQueryResult(
        columns=["created_quiz_count"],
        rows=[{"created_quiz_count": 0}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You haven't created any quizzes yet."
    )


def test_formats_follower_count_as_text():
    result = ChatbotQueryResult(
        columns=["follower_count"],
        rows=[{"follower_count": 4}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You have 4 followers."


def test_formats_single_follower_as_text():
    result = ChatbotQueryResult(
        columns=["follower_count"],
        rows=[{"follower_count": 1}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == "You have 1 follower."


def test_formats_zero_followers_as_text():
    result = ChatbotQueryResult(
        columns=["follower_count"],
        rows=[{"follower_count": 0}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You don't have any followers yet."
    )


def test_formats_following_count_as_text():
    result = ChatbotQueryResult(
        columns=["following_count"],
        rows=[{"following_count": 4}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You're following 4 people."
    )


def test_formats_single_following_as_text():
    result = ChatbotQueryResult(
        columns=["following_count"],
        rows=[{"following_count": 1}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You're following 1 person."
    )


def test_formats_zero_following_as_text():
    result = ChatbotQueryResult(
        columns=["following_count"],
        rows=[{"following_count": 0}],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "You're not following anyone yet."
    )


def test_formats_user_connection_list_as_table():
    result = ChatbotQueryResult(
        columns=[
            "user_id",
            "display_name",
        ],
        rows=[
            {
                "user_id": "user-1",
                "display_name": "Alice",
            },
            {
                "user_id": "user-2",
                "display_name": "Bob",
            },
        ],
        total_rows=2,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == "Here are 2 people."
    assert response.columns == result.columns
    assert response.rows == result.rows
    assert response.total_rows == 2


def test_formats_single_user_connection_as_table():
    result = ChatbotQueryResult(
        columns=[
            "user_id",
            "display_name",
        ],
        rows=[
            {
                "user_id": "user-1",
                "display_name": "Alice",
            },
        ],
        total_rows=1,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "table"
    assert response.message == "Here is 1 person."


def test_formats_empty_user_connection_list_as_text():
    result = ChatbotQueryResult(
        columns=[
            "user_id",
            "display_name",
        ],
        rows=[],
        total_rows=0,
    )

    response = format_chatbot_query_result(result)

    assert response.type == "text"
    assert response.message == (
        "There aren't any users to show for "
        "this connection list yet."
    )
