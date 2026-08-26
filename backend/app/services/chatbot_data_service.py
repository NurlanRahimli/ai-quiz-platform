import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.services.quiz_grading import grade_attempt_answer


@dataclass(frozen=True)
class ChatbotQuizSummary:
    quiz_id: uuid.UUID
    title: str
    creator_name: str
    category: str | None
    attempt_count: int
    average_score: float | None


@dataclass(frozen=True)
class ChatbotQuestionPerformanceRow:
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    question_id: uuid.UUID
    question_text: str
    question_type: str
    submitted_at: datetime
    is_correct: bool


@dataclass(frozen=True)
class ChatbotAttemptRow:
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    creator_name: str
    category: str | None
    submitted_at: datetime
    score_percentage: float | None


def get_user_quiz_summaries(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[ChatbotQuizSummary]:
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
        .where(QuizAttempt.user_id == user_id)
        .order_by(
            QuizAttempt.submitted_at.desc(),
            QuizAttempt.id.desc(),
        )
    ).all()

    if not attempts:
        return []

    creator_ids = {
        attempt.quiz.owner_id
        for attempt in attempts
    }

    creators = db.scalars(
        select(User).where(User.id.in_(creator_ids))
    ).all()

    creator_names = {
        creator.id: creator.display_name
        for creator in creators
    }

    summaries: dict[uuid.UUID, ChatbotQuizSummary] = {}
    score_totals: dict[uuid.UUID, float] = {}
    graded_attempt_counts: dict[uuid.UUID, int] = {}

    for attempt in attempts:
        score = 0
        gradable_questions = 0

        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is None:
                continue

            gradable_questions += 1

            if is_correct:
                score += 1

        score_percentage = (
            (score / gradable_questions) * 100
            if gradable_questions > 0
            else None
        )

        existing = summaries.get(attempt.quiz_id)

        if existing is None:
            summaries[attempt.quiz_id] = ChatbotQuizSummary(
                quiz_id=attempt.quiz_id,
                title=attempt.quiz.title,
                creator_name=creator_names.get(
                    attempt.quiz.owner_id,
                    "Unknown",
                ),
                category=attempt.quiz.category,
                attempt_count=1,
                average_score=None,
            )
        else:
            summaries[attempt.quiz_id] = ChatbotQuizSummary(
                quiz_id=existing.quiz_id,
                title=existing.title,
                creator_name=existing.creator_name,
                category=existing.category,
                attempt_count=existing.attempt_count + 1,
                average_score=existing.average_score,
            )

        if score_percentage is not None:
            score_totals[attempt.quiz_id] = (
                score_totals.get(attempt.quiz_id, 0.0)
                + score_percentage
            )
            graded_attempt_counts[attempt.quiz_id] = (
                graded_attempt_counts.get(attempt.quiz_id, 0)
                + 1
            )

    results: list[ChatbotQuizSummary] = []

    for quiz_id, summary in summaries.items():
        graded_count = graded_attempt_counts.get(quiz_id, 0)

        average_score = (
            round(score_totals[quiz_id] / graded_count, 2)
            if graded_count > 0
            else None
        )

        results.append(
            ChatbotQuizSummary(
                quiz_id=summary.quiz_id,
                title=summary.title,
                creator_name=summary.creator_name,
                category=summary.category,
                attempt_count=summary.attempt_count,
                average_score=average_score,
            )
        )

    return results


def get_user_attempt_rows(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[ChatbotAttemptRow]:
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
        .where(QuizAttempt.user_id == user_id)
        .order_by(
            QuizAttempt.submitted_at.desc(),
            QuizAttempt.id.desc(),
        )
    ).all()

    if not attempts:
        return []

    creator_ids = {
        attempt.quiz.owner_id
        for attempt in attempts
    }

    creators = db.scalars(
        select(User).where(User.id.in_(creator_ids))
    ).all()

    creator_names = {
        creator.id: creator.display_name
        for creator in creators
    }

    rows: list[ChatbotAttemptRow] = []

    for attempt in attempts:
        score = 0
        gradable_questions = 0

        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is None:
                continue

            gradable_questions += 1

            if is_correct:
                score += 1

        score_percentage = (
            round((score / gradable_questions) * 100, 2)
            if gradable_questions > 0
            else None
        )

        rows.append(
            ChatbotAttemptRow(
                attempt_id=attempt.id,
                quiz_id=attempt.quiz_id,
                quiz_title=attempt.quiz.title,
                creator_name=creator_names.get(
                    attempt.quiz.owner_id,
                    "Unknown",
                ),
                category=attempt.quiz.category,
                submitted_at=attempt.submitted_at,
                score_percentage=score_percentage,
            )
        )

    return rows

def get_user_question_performance_rows(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[ChatbotQuestionPerformanceRow]:
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
        .where(QuizAttempt.user_id == user_id)
        .order_by(
            QuizAttempt.submitted_at.desc(),
            QuizAttempt.id.desc(),
        )
    ).all()

    rows: list[ChatbotQuestionPerformanceRow] = []

    for attempt in attempts:
        for answer in attempt.answers:
            is_correct = grade_attempt_answer(
                answer.question,
                answer,
            )

            if is_correct is None:
                continue

            rows.append(
                ChatbotQuestionPerformanceRow(
                    attempt_id=attempt.id,
                    quiz_id=attempt.quiz_id,
                    quiz_title=attempt.quiz.title,
                    question_id=answer.question_id,
                    question_text=answer.question.text,
                    question_type=answer.question.question_type,
                    submitted_at=attempt.submitted_at,
                    is_correct=is_correct,
                )
            )

    return rows

