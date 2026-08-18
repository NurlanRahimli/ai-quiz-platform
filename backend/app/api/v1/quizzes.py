import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate,
    QuizDetailResponse,
    QuizResponse,
    QuizTakeResponse,
    QuizUpdate,
)
from app.models.question import Question

router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


@router.post(
    "",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Quiz:
    quiz = Quiz(
        owner_id=current_user.id,
        title=quiz_data.title,
        description=quiz_data.description,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


@router.get(
    "",
    response_model=list[QuizResponse],
)
def list_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Quiz]:
    return list(
        db.scalars(
            select(Quiz)
            .where(Quiz.owner_id == current_user.id)
            .order_by(Quiz.created_at.desc())
        )
    )


@router.get(
    "/{quiz_id}/take",
    response_model=QuizTakeResponse,
)
def take_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Quiz:
    quiz = db.scalar(
        select(Quiz)
        .options(
            selectinload(Quiz.questions)
            .selectinload(Question.answer_choices)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return quiz


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
)
def get_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Quiz:
    quiz = db.scalar(
        select(Quiz)
        .options(
            selectinload(Quiz.questions)
            .selectinload(Question.answer_choices)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.owner_id == current_user.id,
        )
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return quiz


@router.patch(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def update_quiz(
    quiz_id: uuid.UUID,
    quiz_data: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Quiz:
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

    update_data = quiz_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(quiz, field, value)

    db.commit()
    db.refresh(quiz)

    return quiz


@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
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

    db.delete(quiz)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)