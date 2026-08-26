import uuid
from datetime import datetime, timezone

from app.services.chatbot_data_service import ChatbotAttemptRow
from app.services.chatbot_query_service import (
    ChatbotQuery,
    ChatbotQueryFilters,
    execute_chatbot_query,
)


def make_row(
    *,
    quiz_id: uuid.UUID,
    quiz_title: str,
    creator_name: str,
    category: str | None,
    score_percentage: float | None,
    submitted_at: datetime | None = None,
) -> ChatbotAttemptRow:
    return ChatbotAttemptRow(
        attempt_id=uuid.uuid4(),
        quiz_id=quiz_id,
        quiz_title=quiz_title,
        creator_name=creator_name,
        category=category,
        submitted_at=submitted_at
        or datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        score_percentage=score_percentage,
    )


def test_query_total_attempt_count():
    python_id = uuid.uuid4()
    math_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=50.0,
        ),
        make_row(
            quiz_id=math_id,
            quiz_title="Algebra",
            creator_name="Bob",
            category="Mathematics",
            score_percentage=80.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(metrics=("attempt_count",)),
    )

    assert result.columns == ["attempt_count"]
    assert result.rows == [{"attempt_count": 3}]
    assert result.total_rows == 1


def test_query_distinct_quiz_count():
    python_id = uuid.uuid4()
    math_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=50.0,
        ),
        make_row(
            quiz_id=math_id,
            quiz_title="Algebra",
            creator_name="Bob",
            category="Mathematics",
            score_percentage=80.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(metrics=("quiz_count",)),
    )

    assert result.rows == [{"quiz_count": 2}]


def test_query_attempt_count_grouped_by_quiz():
    python_id = uuid.uuid4()
    math_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=50.0,
        ),
        make_row(
            quiz_id=math_id,
            quiz_title="Algebra",
            creator_name="Bob",
            category="Mathematics",
            score_percentage=80.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("attempt_count",),
            group_by="quiz",
        ),
    )

    assert result.total_rows == 2

    by_title = {
        row["quiz_title"]: row
        for row in result.rows
    }

    assert by_title["Python"]["creator_name"] == "Alice"
    assert by_title["Python"]["category"] == "Programming"
    assert by_title["Python"]["attempt_count"] == 2

    assert by_title["Algebra"]["creator_name"] == "Bob"
    assert by_title["Algebra"]["attempt_count"] == 1


def test_query_average_score_grouped_by_quiz():
    python_id = uuid.uuid4()
    math_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=python_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=50.0,
        ),
        make_row(
            quiz_id=math_id,
            quiz_title="Algebra",
            creator_name="Bob",
            category="Mathematics",
            score_percentage=90.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("average_score",),
            group_by="quiz",
        ),
    )

    by_title = {
        row["quiz_title"]: row
        for row in result.rows
    }

    assert by_title["Python"]["average_score"] == 75.0
    assert by_title["Algebra"]["average_score"] == 90.0


def test_query_average_score_grouped_by_category():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="JavaScript",
            creator_name="Bob",
            category="Programming",
            score_percentage=60.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Biology",
            creator_name="Carol",
            category="Science",
            score_percentage=90.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("average_score",),
            group_by="category",
        ),
    )

    by_category = {
        row["category"]: row["average_score"]
        for row in result.rows
    }

    assert by_category["Programming"] == 80.0
    assert by_category["Science"] == 90.0


def test_query_filters_by_category_case_insensitively():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Biology",
            creator_name="Bob",
            category="Science",
            score_percentage=80.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("attempt_count",),
            filters=ChatbotQueryFilters(
                category="programming",
            ),
        ),
    )

    assert result.rows == [{"attempt_count": 1}]


def test_query_filters_by_date_range():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=70.0,
            submitted_at=datetime(
                2026,
                7,
                15,
                tzinfo=timezone.utc,
            ),
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=90.0,
            submitted_at=datetime(
                2026,
                8,
                15,
                tzinfo=timezone.utc,
            ),
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("average_score",),
            filters=ChatbotQueryFilters(
                date_from=datetime(
                    2026,
                    8,
                    1,
                    tzinfo=timezone.utc,
                ),
                date_to=datetime(
                    2026,
                    8,
                    31,
                    23,
                    59,
                    59,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
    )

    assert result.rows == [{"average_score": 90.0}]


def test_query_sort_and_limit():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Python",
            creator_name="Alice",
            category="Programming",
            score_percentage=70.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Biology",
            creator_name="Bob",
            category="Science",
            score_percentage=95.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Algebra",
            creator_name="Carol",
            category="Mathematics",
            score_percentage=80.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=("average_score",),
            group_by="quiz",
            sort_by="average_score",
            sort_direction="desc",
            limit=2,
        ),
    )

    assert result.total_rows == 3
    assert len(result.rows) == 2

    assert result.rows[0]["quiz_title"] == "Biology"
    assert result.rows[0]["average_score"] == 95.0

    assert result.rows[1]["quiz_title"] == "Algebra"
    assert result.rows[1]["average_score"] == 80.0


def test_query_multiple_metrics_grouped_by_quiz():
    python_id = uuid.uuid4()
    biology_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            score_percentage=100.0,
        ),
        make_row(
            quiz_id=python_id,
            quiz_title="Python Basics",
            creator_name="Alice",
            category="Programming",
            score_percentage=50.0,
        ),
        make_row(
            quiz_id=biology_id,
            quiz_title="Biology",
            creator_name="Bob",
            category="Science",
            score_percentage=90.0,
        ),
    ]

    result = execute_chatbot_query(
        rows,
        ChatbotQuery(
            metrics=(
                "attempt_count",
                "average_score",
            ),
            group_by="quiz",
            sort_by="attempt_count",
            sort_direction="desc",
        ),
    )

    assert result.total_rows == 2

    by_title = {
        row["quiz_title"]: row
        for row in result.rows
    }

    python = by_title["Python Basics"]

    assert python["creator_name"] == "Alice"
    assert python["category"] == "Programming"
    assert python["attempt_count"] == 2
    assert python["average_score"] == 75.0

    biology = by_title["Biology"]

    assert biology["creator_name"] == "Bob"
    assert biology["attempt_count"] == 1
    assert biology["average_score"] == 90.0

