import uuid
from datetime import datetime, timezone

from app.services.chatbot_data_service import (
    ChatbotQuestionPerformanceRow,
)
from app.services.chatbot_study_recommendation_service import (
    build_study_recommendations,
)


def make_row(
    *,
    quiz_id,
    quiz_title,
    question_id,
    question_text,
    is_correct,
):
    return ChatbotQuestionPerformanceRow(
        attempt_id=uuid.uuid4(),
        quiz_id=quiz_id,
        quiz_title=quiz_title,
        question_id=question_id,
        question_text=question_text,
        question_type="multiple_choice",
        submitted_at=datetime.now(timezone.utc),
        is_correct=is_correct,
    )


def test_build_study_recommendations_prioritizes_repeated_misses():
    quiz_id = uuid.uuid4()
    weak_question = uuid.uuid4()
    second_question = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            question_id=weak_question,
            question_text="What does let do?",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            question_id=weak_question,
            question_text="What does let do?",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            question_id=weak_question,
            question_text="What does let do?",
            is_correct=True,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript Fundamentals",
            question_id=second_question,
            question_text="What does const do?",
            is_correct=False,
        ),
    ]

    result = build_study_recommendations(rows)

    assert len(result) == 2

    assert result[0].priority == 1
    assert result[0].question_text == "What does let do?"
    assert result[0].wrong_count == 2
    assert result[0].attempt_count == 3
    assert result[0].miss_rate == 66.67

    assert result[1].priority == 2
    assert result[1].question_text == "What does const do?"


def test_build_study_recommendations_filters_quiz():
    javascript_id = uuid.uuid4()
    biology_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=javascript_id,
            quiz_title="JavaScript Fundamentals",
            question_id=uuid.uuid4(),
            question_text="JavaScript question",
            is_correct=False,
        ),
        make_row(
            quiz_id=biology_id,
            quiz_title="Biology Basics",
            question_id=uuid.uuid4(),
            question_text="Biology question",
            is_correct=False,
        ),
    ]

    result = build_study_recommendations(
        rows,
        quiz_title="javascript",
    )

    assert len(result) == 1
    assert result[0].quiz_title == (
        "JavaScript Fundamentals"
    )
    assert result[0].question_text == (
        "JavaScript question"
    )


def test_build_study_recommendations_excludes_perfect_questions():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=uuid.uuid4(),
            question_text="Already mastered",
            is_correct=True,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=uuid.uuid4(),
            question_text="Needs review",
            is_correct=False,
        ),
    ]

    result = build_study_recommendations(rows)

    assert len(result) == 1
    assert result[0].question_text == "Needs review"


def test_build_study_recommendations_builds_reason():
    quiz_id = uuid.uuid4()
    question_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a list?",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a list?",
            is_correct=False,
        ),
    ]

    result = build_study_recommendations(rows)

    assert len(result) == 1
    assert result[0].reason == (
        "You missed this question 2 times "
        "across 2 attempts (100% miss rate)."
    )


def test_build_study_recommendations_respects_limit():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=uuid.uuid4(),
            question_text=f"Question {index}",
            is_correct=False,
        )
        for index in range(8)
    ]

    result = build_study_recommendations(
        rows,
        limit=3,
    )

    assert len(result) == 3
    assert [
        recommendation.priority
        for recommendation in result
    ] == [1, 2, 3]
