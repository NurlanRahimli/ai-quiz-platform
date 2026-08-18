import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.answer_choice import AnswerChoice
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.question import (
    QuestionCreate,
    QuestionResponse,
    WrittenAnswerQuestionCreate,
)


router = APIRouter(
    prefix="/quizzes",
    tags=["Questions"],
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