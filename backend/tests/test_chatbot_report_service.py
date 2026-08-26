import uuid
from datetime import datetime, timezone

from app.services.chatbot_data_service import ChatbotAttemptRow
from app.services.chatbot_report_service import build_monthly_report


def make_row(
    *,
    quiz_id,
    category,
    submitted_at,
    score,
):
    return ChatbotAttemptRow(
        attempt_id=uuid.uuid4(),
        quiz_id=quiz_id,
        quiz_title="Test Quiz",
        creator_name="Test Creator",
        category=category,
        submitted_at=submitted_at,
        score_percentage=score,
    )


def test_build_monthly_report_calculates_current_metrics():
    python_id = uuid.uuid4()
    math_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=python_id,
            category="Programming",
            submitted_at=datetime(
                2026, 8, 5, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
        make_row(
            quiz_id=python_id,
            category="Programming",
            submitted_at=datetime(
                2026, 8, 10, tzinfo=timezone.utc
            ),
            score=100.0,
        ),
        make_row(
            quiz_id=math_id,
            category="Mathematics",
            submitted_at=datetime(
                2026, 8, 15, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=8,
    )

    assert report.attempt_count == 3
    assert report.quiz_count == 2
    assert report.average_score == 80.0


def test_build_monthly_report_compares_previous_month():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            category="Programming",
            submitted_at=datetime(
                2026, 7, 10, tzinfo=timezone.utc
            ),
            score=50.0,
        ),
        make_row(
            quiz_id=quiz_id,
            category="Programming",
            submitted_at=datetime(
                2026, 7, 12, tzinfo=timezone.utc
            ),
            score=70.0,
        ),
        make_row(
            quiz_id=quiz_id,
            category="Programming",
            submitted_at=datetime(
                2026, 8, 10, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
        make_row(
            quiz_id=quiz_id,
            category="Programming",
            submitted_at=datetime(
                2026, 8, 12, tzinfo=timezone.utc
            ),
            score=90.0,
        ),
        make_row(
            quiz_id=quiz_id,
            category="Programming",
            submitted_at=datetime(
                2026, 8, 14, tzinfo=timezone.utc
            ),
            score=100.0,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=8,
    )

    assert report.attempt_count == 3
    assert report.previous_attempt_count == 2
    assert report.attempt_change == 1

    assert report.average_score == 90.0
    assert report.previous_average_score == 60.0
    assert report.score_change == 30.0


def test_build_monthly_report_finds_strongest_and_weakest_category():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            category="Programming",
            submitted_at=datetime(
                2026, 8, 5, tzinfo=timezone.utc
            ),
            score=40.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            category="Programming",
            submitted_at=datetime(
                2026, 8, 6, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            category="Mathematics",
            submitted_at=datetime(
                2026, 8, 7, tzinfo=timezone.utc
            ),
            score=90.0,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=8,
    )

    assert report.strongest_category is not None
    assert report.strongest_category.category == "Mathematics"
    assert report.strongest_category.average_score == 90.0

    assert report.weakest_category is not None
    assert report.weakest_category.category == "Programming"
    assert report.weakest_category.average_score == 50.0


def test_build_monthly_report_handles_ungraded_attempts():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            category="Writing",
            submitted_at=datetime(
                2026, 8, 5, tzinfo=timezone.utc
            ),
            score=None,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=8,
    )

    assert report.attempt_count == 1
    assert report.quiz_count == 1
    assert report.average_score is None
    assert report.strongest_category is None
    assert report.weakest_category is None


def test_build_monthly_report_handles_no_attempts():
    report = build_monthly_report(
        [],
        year=2026,
        month=8,
    )

    assert report.attempt_count == 0
    assert report.quiz_count == 0
    assert report.average_score is None
    assert report.previous_attempt_count == 0
    assert report.previous_average_score is None
    assert report.attempt_change == 0
    assert report.quiz_change == 0
    assert report.score_change is None
    assert report.strongest_category is None
    assert report.weakest_category is None


def test_build_monthly_report_handles_january_previous_month():
    quiz_id = uuid.uuid4()

    rows = [
        make_row(
            quiz_id=quiz_id,
            category="Science",
            submitted_at=datetime(
                2025, 12, 20, tzinfo=timezone.utc
            ),
            score=70.0,
        ),
        make_row(
            quiz_id=quiz_id,
            category="Science",
            submitted_at=datetime(
                2026, 1, 10, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=1,
    )

    assert report.average_score == 80.0
    assert report.previous_average_score == 70.0
    assert report.score_change == 10.0

def test_build_monthly_report_excludes_uncategorized_from_category_insights():
    rows = [
        make_row(
            quiz_id=uuid.uuid4(),
            category=None,
            submitted_at=datetime(
                2026, 8, 5, tzinfo=timezone.utc
            ),
            score=100.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            category="Programming",
            submitted_at=datetime(
                2026, 8, 10, tzinfo=timezone.utc
            ),
            score=60.0,
        ),
        make_row(
            quiz_id=uuid.uuid4(),
            category="Science",
            submitted_at=datetime(
                2026, 8, 15, tzinfo=timezone.utc
            ),
            score=80.0,
        ),
    ]

    report = build_monthly_report(
        rows,
        year=2026,
        month=8,
    )

    # Uncategorized still contributes to the overall report.
    assert report.attempt_count == 3
    assert report.average_score == 80.0

    # But only real categories can become performance insights.
    assert report.strongest_category is not None
    assert report.strongest_category.category == "Science"

    assert report.weakest_category is not None
    assert report.weakest_category.category == "Programming"

