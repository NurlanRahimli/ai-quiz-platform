import uuid
from datetime import datetime, timezone

from app.services.chatbot_data_service import (
    ChatbotQuestionPerformanceRow,
)
from app.services.chatbot_question_performance_service import (
    summarize_question_performance,
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


def test_summarize_question_performance_counts_repeated_misses():
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
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            question_id=question_id,
            question_text="What is a list?",
            is_correct=True,
        ),
    ]

    summaries = summarize_question_performance(rows)

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.attempt_count == 3
    assert summary.correct_count == 1
    assert summary.wrong_count == 2
    assert summary.miss_rate == 66.67


def test_summarize_question_performance_orders_most_missed_first():
    quiz_id = uuid.uuid4()
    first_question = uuid.uuid4()
    second_question = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            question_id=first_question,
            question_text="Question one",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            question_id=first_question,
            question_text="Question one",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            question_id=second_question,
            question_text="Question two",
            is_correct=False,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            question_id=second_question,
            question_text="Question two",
            is_correct=True,
        ),
    ]

    summaries = summarize_question_performance(
        rows,
        wrong_only=True,
    )

    assert len(summaries) == 2
    assert summaries[0].question_text == "Question one"
    assert summaries[0].wrong_count == 2
    assert summaries[1].question_text == "Question two"
    assert summaries[1].wrong_count == 1


def test_summarize_question_performance_filters_by_quiz_title():
    python_id = uuid.uuid4()
    biology_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python Fundamentals",
            question_id=uuid.uuid4(),
            question_text="Python question",
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

    summaries = summarize_question_performance(
        rows,
        quiz_title="python",
        wrong_only=True,
    )

    assert len(summaries) == 1
    assert summaries[0].quiz_title == "Python Fundamentals"
    assert summaries[0].question_text == "Python question"


def test_summarize_question_performance_wrong_only_excludes_perfect_questions():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Science",
            question_id=uuid.uuid4(),
            question_text="Always correct",
            is_correct=True,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Science",
            question_id=uuid.uuid4(),
            question_text="Needs work",
            is_correct=False,
        ),
    ]

    summaries = summarize_question_performance(
        rows,
        wrong_only=True,
    )

    assert len(summaries) == 1
    assert summaries[0].question_text == "Needs work"
    assert summaries[0].wrong_count == 1
    assert summaries[0].miss_rate == 100.0
