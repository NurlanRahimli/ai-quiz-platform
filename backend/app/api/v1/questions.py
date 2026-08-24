import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.question import (
    MathWorkQuestionCreate,
    MultipleChoiceQuestionUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionTextUpdate,
    WrittenAnswerQuestionCreate,
    MathWorkQuestionUpdate
)
from app.services.math_validation import (
    MathValidationError,
    parse_math_expression,
)

from pydantic import ValidationError

router = APIRouter(
    prefix="/quizzes",
    tags=["Questions"],
)


MAX_QUESTIONS_PER_QUIZ = 30


def ensure_question_limit(
    db: Session,
    quiz_id: uuid.UUID,
) -> None:
    question_count = db.scalar(
        select(func.count(Question.id)).where(
            Question.quiz_id == quiz_id
        )
    )

    if (question_count or 0) >= MAX_QUESTIONS_PER_QUIZ:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quiz can have a maximum of 30 questions",
        )


@router.post(
    "/{quiz_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_multiple_choice_question(
    quiz_id: uuid.UUID,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
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

    ensure_question_limit(db, quiz.id)

    current_position = db.scalar(
        select(func.max(Question.position)).where(
            Question.quiz_id == quiz.id
        )
    )

    question = Question(
        quiz_id=quiz.id,
        text=question_data.text,
        question_type="multiple_choice",
        position=(current_position or 0) + 1,
    )

    question.answer_choices = [
        AnswerChoice(
            text=choice.text,
            is_correct=choice.is_correct,
            position=index,
        )
        for index, choice in enumerate(
            question_data.choices,
            start=1,
        )
    ]

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.post(
    "/{quiz_id}/questions/written",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_written_answer_question(
    quiz_id: uuid.UUID,
    question_data: WrittenAnswerQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
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

    ensure_question_limit(db, quiz.id)

    current_position = db.scalar(
        select(func.max(Question.position)).where(
            Question.quiz_id == quiz.id
        )
    )

    question = Question(
        quiz_id=quiz.id,
        text=question_data.text,
        question_type="written_answer",
        position=(current_position or 0) + 1,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.post(
    "/{quiz_id}/questions/math-work",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_math_work_question(
    quiz_id: uuid.UUID,
    question_data: MathWorkQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
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

    ensure_question_limit(db, quiz.id)

    current_position = db.scalar(
        select(func.max(Question.position)).where(
            Question.quiz_id == quiz.id
        )
    )

    try:
        parse_math_expression(question_data.expected_answer)
    except MathValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Expected answer must be a valid math expression",
        ) from exc

    question = Question(
        quiz_id=quiz.id,
        text=question_data.text,
        question_type="math_work",
        expected_answer=question_data.expected_answer,
        position=(current_position or 0) + 1,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.patch(
    "/{quiz_id}/questions/{question_id}",
    response_model=QuestionResponse,
)
def update_question(
    quiz_id: uuid.UUID,
    question_id: uuid.UUID,
    question_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Question:
    question = db.scalar(
        select(Question)
        .join(Quiz)
        .where(
            Question.id == question_id,
            Question.quiz_id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    if question.question_type == "multiple_choice":
        try:
            validated = MultipleChoiceQuestionUpdate.model_validate(
                question_data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(include_context=False),
            ) from exc

        question.text = validated.text
        question.answer_choices.clear()

        question.answer_choices.extend(
            AnswerChoice(
                text=choice.text,
                is_correct=choice.is_correct,
                position=index,
            )
            for index, choice in enumerate(
                validated.choices,
                start=1,
            )
        )
    elif question.question_type == "math_work":
        try:
            validated = MathWorkQuestionUpdate.model_validate(
                question_data
            )
            parse_math_expression(validated.expected_answer)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(include_context=False),
            ) from exc
        except MathValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Expected answer must be a valid math expression",
            ) from exc

        question.text = validated.text
        question.expected_answer = validated.expected_answer

    else:
        try:
            validated = QuestionTextUpdate.model_validate(question_data)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(include_context=False),
            ) from exc

        question.text = validated.text

    db.commit()
    db.refresh(question)

    return question


@router.delete(
    "/{quiz_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question(
    quiz_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    question = db.scalar(
        select(Question)
        .join(Quiz)
        .where(
            Question.id == question_id,
            Question.quiz_id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    deleted_position = question.position

    db.delete(question)
    db.flush()

    remaining_questions = list(
        db.scalars(
            select(Question)
            .where(
                Question.quiz_id == quiz_id,
                Question.position > deleted_position,
            )
            .order_by(Question.position)
        )
    )

    for remaining_question in remaining_questions:
        remaining_question.position -= 1

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)