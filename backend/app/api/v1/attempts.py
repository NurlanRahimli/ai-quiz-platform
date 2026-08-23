import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.quiz_attempt_answer import QuizAttemptAnswer
from app.models.user import User
from app.schemas.quiz_attempt import (
    QuizAttemptHistoryItem,
    QuizAttemptResponse,
    QuizAttemptResultAnswer,
    QuizAttemptResultResponse,
    QuizAttemptSubmit,
    QuizAttemptResultChoice,
)
from app.services.quiz_grading import grade_attempt_answer
from app.models.audit_log import AuditLog


router = APIRouter(
    prefix="/quizzes",
    tags=["Quiz Attempts"],
)


@router.post(
    "/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_quiz_attempt(
    quiz_id: uuid.UUID,
    attempt_data: QuizAttemptSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttempt:
    quiz = db.scalar(
        select(Quiz)
        .options(
            selectinload(Quiz.questions)
            .selectinload(Question.answer_choices)
        )
        .where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    questions = {
        question.id: question
        for question in quiz.questions
    }

    submitted_question_ids = [
        answer.question_id
        for answer in attempt_data.answers
    ]

    if len(submitted_question_ids) != len(set(submitted_question_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each question can only be answered once",
        )

    if set(submitted_question_ids) != set(questions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An answer must be provided for every quiz question",
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
    )

    for submitted_answer in attempt_data.answers:
        question = questions[submitted_answer.question_id]

        if question.question_type == "multiple_choice":
            if submitted_answer.text_answer is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Multiple-choice questions cannot include "
                        "a text answer"
                    ),
                )

            valid_choice_ids = {
                choice.id
                for choice in question.answer_choices
            }

            if (
                submitted_answer.selected_choice_id is not None
                and submitted_answer.selected_choice_id not in valid_choice_ids
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Selected answer choice does not belong "
                        "to this question"
                    ),
                )

        elif question.question_type in {
            "written_answer",
            "math_work",
        }:
            if submitted_answer.selected_choice_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot include "
                        "a selected choice"
                    ),
                )

            if (
                submitted_answer.text_answer is not None
                and not submitted_answer.text_answer.strip()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Written and math questions cannot contain "
                        "an empty text answer"
                    ),
                )

            submitted_answer.text_answer = (
                submitted_answer.text_answer.strip()
                if submitted_answer.text_answer is not None
                else None
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported question type",
            )

        attempt.answers.append(
            QuizAttemptAnswer(
                question_id=question.id,
                selected_choice_id=(
                    submitted_answer.selected_choice_id
                ),
                text_answer=submitted_answer.text_answer,
            )
        )


    quiz_creator = db.scalar(
        select(User).where(User.id == quiz.owner_id)
    )

    if quiz_creator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz creator not found",
        )

    audit_log = AuditLog(
        user_id=current_user.id,
        quiz_id=quiz.id,
        action="quiz_completed",
        quiz_title=quiz.title,
        creator_name=quiz_creator.display_name,
    )

    db.add(audit_log)


    db.add(attempt)
    db.commit()

    saved_attempt = db.scalar(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.answers))
        .where(QuizAttempt.id == attempt.id)
    )

    return saved_attempt


@router.get(
    "/{quiz_id}/attempts",
    response_model=list[QuizAttemptHistoryItem],
)
def get_quiz_attempt_history(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuizAttemptHistoryItem]:
    quiz = db.scalar(
        select(Quiz).where(
            Quiz.id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    attempts = db.scalars(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
        .order_by(QuizAttempt.submitted_at.desc())
    ).all()

    history: list[QuizAttemptHistoryItem] = []

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

        history.append(
            QuizAttemptHistoryItem(
                attempt_id=attempt.id,
                submitted_at=attempt.submitted_at,
                score=score,
                gradable_questions=gradable_questions,
                total_questions=len(attempt.answers),
            )
        )

    return history


@router.get(
    "/{quiz_id}/attempts/{attempt_id}/results",
    response_model=QuizAttemptResultResponse,
)
def get_quiz_attempt_results(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizAttemptResultResponse:
    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.question)
            .selectinload(Question.answer_choices),
            selectinload(QuizAttempt.answers)
            .selectinload(QuizAttemptAnswer.selected_choice),
        )
        .where(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    result_answers: list[QuizAttemptResultAnswer] = []
    score = 0
    gradable_questions = 0

    for answer in attempt.answers:
        question = answer.question
        is_correct = grade_attempt_answer(question, answer)

        if is_correct is not None:
            gradable_questions += 1

            if is_correct:
                score += 1

        answer_choices: list[QuizAttemptResultChoice] = []

        if question.question_type == "multiple_choice":
            submitted_answer = (
                answer.selected_choice.text
                if answer.selected_choice
                else ""
            )

            correct_choice = next(
                (
                    choice
                    for choice in question.answer_choices
                    if choice.is_correct
                ),
                None,
            )

            correct_answer = (
                correct_choice.text
                if correct_choice
                else None
            )

            answer_choices = [
                QuizAttemptResultChoice(
                    id=choice.id,
                    text=choice.text,
                    is_correct=choice.is_correct,
                    was_selected=(
                        choice.id == answer.selected_choice_id
                    ),
                    position=choice.position,
                )
                for choice in sorted(
                    question.answer_choices,
                    key=lambda choice: choice.position,
                )
            ]

        elif question.question_type == "math_work":
            submitted_answer = answer.text_answer or ""
            correct_answer = question.expected_answer

        else:
            submitted_answer = answer.text_answer or ""
            correct_answer = None

        result_answers.append(
            QuizAttemptResultAnswer(
                answer_choices=answer_choices,
                question_id=question.id,
                question_text=question.text,
                question_type=question.question_type,
                is_correct=is_correct,
                submitted_answer=submitted_answer,
                correct_answer=correct_answer,
            )
        )

    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        score=score,
        gradable_questions=gradable_questions,
        total_questions=len(attempt.answers),
        answers=result_answers,
    )