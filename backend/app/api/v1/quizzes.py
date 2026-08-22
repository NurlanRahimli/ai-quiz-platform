import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.quiz import Quiz
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate,
    QuizDetailResponse,
    QuizLandingResponse,
    QuizListResponse,
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
        visibility=quiz_data.visibility,
        category=quiz_data.category,
        tags=quiz_data.tags,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


@router.get(
    "",
    response_model=list[QuizListResponse],
)
def list_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuizListResponse]:
    quizzes = list(
        db.scalars(
            select(Quiz)
            .where(Quiz.owner_id == current_user.id)
            .order_by(Quiz.created_at.desc())
        )
    )

    return [
        QuizListResponse(
            id=quiz.id,
            owner_id=quiz.owner_id,
            title=quiz.title,
            description=quiz.description,
            visibility=quiz.visibility,
            category=quiz.category,
            tags=quiz.tags,
            creator_name=current_user.display_name,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )
        for quiz in quizzes
    ]


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
        .where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return quiz


@router.get(
    "/{quiz_id}",
    response_model=QuizLandingResponse,
)
def get_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizLandingResponse:
    quiz = db.scalar(
        select(Quiz).where(Quiz.id == quiz_id)
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    creator = db.get(User, quiz.owner_id)

    if creator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz creator not found",
        )

    question_count = db.scalar(
        select(func.count())
        .select_from(Question)
        .where(Question.quiz_id == quiz.id)
    )

    return QuizLandingResponse(
        id=quiz.id,
        owner_id=quiz.owner_id,
        title=quiz.title,
        description=quiz.description,
        visibility=quiz.visibility,
        category=quiz.category,
        tags=quiz.tags,
        creator_name=creator.display_name,
        question_count=question_count or 0,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


@router.get(
    "/{quiz_id}/edit",
    response_model=QuizDetailResponse,
)
def get_quiz_for_editing(
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