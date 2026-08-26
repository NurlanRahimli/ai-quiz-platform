import uuid
from datetime import datetime, timezone

from app.services.chatbot_data_service import ChatbotAttemptRow
from app.services.chatbot_performance_comparison_service import (
    calculate_performance_trend,
    compare_recent_attempts,
)


def make_row(
    *,
    quiz_id,
    quiz_title,
    submitted_at,
    score,
    category="Programming",
):
    return ChatbotAttemptRow(
        attempt_id=uuid.uuid4(),
        quiz_id=quiz_id,
        quiz_title=quiz_title,
        creator_name="Alice",
        category=category,
        submitted_at=submitted_at,
        score_percentage=score,
    )


def test_compare_recent_attempts_returns_latest_three():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, day, tzinfo=timezone.utc
            ),
            score=score,
        )
        for day, score in [
            (1, 40.0),
            (2, 50.0),
            (3, 70.0),
            (4, 90.0),
        ]
    ]

    result = compare_recent_attempts(
        rows,
        quiz_title="Python Basics",
        limit=3,
    )

    assert len(result) == 3
    assert [
        item.score_percentage
        for item in result
    ] == [90.0, 70.0, 50.0]


def test_compare_recent_attempts_filters_quiz():
    python_id = uuid.uuid4()
    biology_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
        make_row(
            quiz_id=biology_id,
            quiz_title="Biology",
            submitted_at=datetime(
                2026, 8, 2, tzinfo=timezone.utc
            ),
            score=20.0,
            category="Science",
        ),
    ]

    result = compare_recent_attempts(
        rows,
        quiz_title="python",
    )

    assert len(result) == 1
    assert result[0].quiz_title == "Python Basics"


def test_calculate_performance_trend_detects_improvement():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=40.0,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 10, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 20, tzinfo=timezone.utc
            ),
            score=85.0,
        ),
    ]

    result = calculate_performance_trend(
        rows,
        quiz_title="Python Basics",
    )

    assert result is not None
    assert result.direction == "improving"
    assert result.attempt_count == 3
    assert result.first_score == 40.0
    assert result.latest_score == 85.0
    assert result.score_change == 45.0


def test_calculate_performance_trend_detects_decline():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=90.0,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="JavaScript",
            submitted_at=datetime(
                2026, 8, 20, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
    ]

    result = calculate_performance_trend(
        rows,
        quiz_title="JavaScript",
    )

    assert result is not None
    assert result.direction == "declining"
    assert result.score_change == -30.0


def test_calculate_performance_trend_detects_stable():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Science",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=75.0,
            category="Science",
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Science",
            submitted_at=datetime(
                2026, 8, 20, tzinfo=timezone.utc
            ),
            score=75.0,
            category="Science",
        ),
    ]

    result = calculate_performance_trend(
        rows,
        quiz_title="Science",
    )

    assert result is not None
    assert result.direction == "stable"
    assert result.score_change == 0.0


def test_single_attempt_has_insufficient_data():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=80.0,
        )
    ]

    result = calculate_performance_trend(
        rows,
        quiz_title="Python Basics",
    )

    assert result is not None
    assert result.direction == "insufficient_data"
    assert result.score_change is None


def test_trend_ignores_ungraded_attempts():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=None,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 2, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
        make_row(
            quiz_id=quiz_id,
            quiz_title="Python Basics",
            submitted_at=datetime(
                2026, 8, 3, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
    ]

    result = calculate_performance_trend(
        rows,
        quiz_title="Python Basics",
    )

    assert result is not None
    assert result.attempt_count == 2
    assert result.first_score == 60.0
    assert result.latest_score == 80.0
    assert result.score_change == 20.0


def test_trend_can_filter_by_category():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Python",
            submitted_at=datetime(
                2026, 8, 1, tzinfo=timezone.utc
            ),
            score=50.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="JavaScript",
            submitted_at=datetime(
                2026, 8, 10, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            quiz_title="Biology",
            submitted_at=datetime(
                2026, 8, 20, tzinfo=timezone.utc
            ),
            score=10.0,
            category="Science",
        ),
    ]

    result = calculate_performance_trend(
        rows,
        category="Programming",
    )

    assert result is not None
    assert result.attempt_count == 2
    assert result.first_score == 50.0
    assert result.latest_score == 80.0
    assert result.direction == "improving"
