from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timedelta, timezone

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCategoryPerformance,
    DashboardPerformancePoint,
    DashboardRecentQuiz,
    DashboardResponse,
    DashboardStats,
)
from app.services.quiz_grading import grade_attempt_answer


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    total_quizzes = db.scalar(
        select(func.count(Quiz.id)).where(
            Quiz.owner_id == current_user.id,
        )
    ) or 0

    attempts = db.scalars(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.quiz),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(
            QuizAttempt.submitted_at.desc(),
            QuizAttempt.id.desc(),
        )
    ).all()

    score_percentages: list[float] = []
    recent_quizzes: list[DashboardRecentQuiz] = []
    recent_quiz_ids: set = set()
    category_attempt_counts: dict[str, int] = {}
    category_score_totals: dict[str, float] = {}
    category_graded_attempt_counts: dict[str, int] = {}
    attempt_score_percentages: dict[object, float | None] = {}

    for attempt in attempts:
        score = 0
        gradable_questions = 0

        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is not None:
                gradable_questions += 1

                if is_correct:
                    score += 1

        score_percentage = (
            round(
                (score / gradable_questions) * 100,
                2,
            )
            if gradable_questions > 0
            else None
        )

        attempt_score_percentages[attempt.id] = score_percentage

        if score_percentage is not None:
            score_percentages.append(score_percentage)

        category = attempt.quiz.category

        if category:
            category_attempt_counts[category] = (
                category_attempt_counts.get(category, 0) + 1
            )

            if score_percentage is not None:
                category_score_totals[category] = (
                    category_score_totals.get(category, 0.0)
                    + score_percentage
                )

                category_graded_attempt_counts[category] = (
                    category_graded_attempt_counts.get(category, 0)
                    + 1
                )
        
        score_percentage = (
            round(
                (score / gradable_questions) * 100,
                2,
            )
            if gradable_questions > 0
            else None
        )

        if (
            attempt.quiz_id not in recent_quiz_ids
            and len(recent_quizzes) < 5
        ):
            recent_quiz_ids.add(attempt.quiz_id)

            recent_quizzes.append(
                DashboardRecentQuiz(
                    quiz_id=attempt.quiz_id,
                    quiz_title=attempt.quiz.title,
                    quiz_category=attempt.quiz.category,
                    latest_attempt_id=attempt.id,
                    latest_submitted_at=attempt.submitted_at,
                    score_percentage=score_percentage,
                )
            )


    top_categories: list[DashboardCategoryPerformance] = []

    sorted_categories = sorted(
        category_attempt_counts,
        key=lambda category: (
            -category_attempt_counts[category],
            -(
                category_score_totals.get(category, 0.0)
                / category_graded_attempt_counts.get(category, 1)
            ),
            category.lower(),
        ),
    )

    for category in sorted_categories[:3]:
        graded_attempt_count = (
            category_graded_attempt_counts.get(category, 0)
        )

        category_average = (
            round(
                category_score_totals[category]
                / graded_attempt_count,
                2,
            )
            if graded_attempt_count > 0
            else None
        )

        top_categories.append(
            DashboardCategoryPerformance(
                category=category,
                average_score=category_average,
                attempt_count=category_attempt_counts[category],
            )
        )


    one_year_ago = datetime.now(timezone.utc).replace(
        tzinfo=None,
    ) - timedelta(days=365)

    performance_scores: list[tuple[datetime, float]] = []

    for attempt in reversed(attempts):
        submitted_at = attempt.submitted_at

        if submitted_at.tzinfo is not None:
            submitted_at = submitted_at.astimezone(
                timezone.utc,
            ).replace(tzinfo=None)

        if submitted_at < one_year_ago:
            continue

        score_percentage = attempt_score_percentages[attempt.id]

        if score_percentage is None:
            continue

        performance_scores.append(
            (
                attempt.submitted_at,
                score_percentage,
            )
        )

    performance: list[DashboardPerformancePoint] = []
    running_total = 0.0

    for index, (submitted_at, score) in enumerate(
        performance_scores,
        start=1,
    ):
        running_total += score

        performance.append(
            DashboardPerformancePoint(
                submitted_at=submitted_at,
                score=score,
                average_score=round(
                    running_total / index,
                    2,
                ),
            )
        )

    average_score = (
        round(
            sum(score_percentages) / len(score_percentages),
            2,
        )
        if score_percentages
        else None
    )

    quizzes_taken = len(
        {
            attempt.quiz_id
            for attempt in attempts
        }
    )

    return DashboardResponse(
        stats=DashboardStats(
            total_quizzes=total_quizzes,
            average_score=average_score,
            quizzes_taken=quizzes_taken,
        ),
        recent_quizzes=recent_quizzes,
        performance=performance,
        top_categories=top_categories,
    )