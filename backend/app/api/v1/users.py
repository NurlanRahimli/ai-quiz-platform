import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.quiz import (
    QuizDiscoveryResponse,
    QuizListResponse,
)
from app.schemas.user import (
    PublicUserProfileResponse,
    UserQuizPageResponse,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)
@router.get(
    "/me/quizzes",
    response_model=UserQuizPageResponse,
)
def get_current_user_quizzes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserQuizPageResponse:
    total = db.scalar(
        select(func.count(Quiz.id)).where(
            Quiz.owner_id == current_user.id,
        )
    ) or 0

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    rows = list(
        db.scalars(
            select(Quiz)
            .where(Quiz.owner_id == current_user.id)
            .order_by(Quiz.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )

    quizzes = [
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
        for quiz in rows
    ]

    return UserQuizPageResponse(
        quizzes=quizzes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{user_id}/profile",
    response_model=PublicUserProfileResponse,
)
def get_public_user_profile(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PublicUserProfileResponse:
    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    public_quiz_count = db.scalar(
        select(func.count(Quiz.id)).where(
            Quiz.owner_id == user.id,
            Quiz.visibility == "public",
        )
    ) or 0

    total_pages = (
        (public_quiz_count + page_size - 1) // page_size
        if public_quiz_count > 0
        else 0
    )

    offset = (page - 1) * page_size

    rows = db.execute(
        select(
            Quiz,
            func.count(func.distinct(Question.id)).label(
                "question_count"
            ),
            func.count(func.distinct(QuizAttempt.id)).label(
                "attempt_count"
            ),
        )
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .outerjoin(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(
            Quiz.owner_id == user.id,
            Quiz.visibility == "public",
        )
        .group_by(Quiz.id)
        .order_by(Quiz.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    quizzes = [
        QuizDiscoveryResponse(
            id=quiz.id,
            owner_id=quiz.owner_id,
            title=quiz.title,
            description=quiz.description,
            visibility=quiz.visibility,
            category=quiz.category,
            tags=quiz.tags,
            creator_name=user.display_name,
            question_count=question_count,
            attempt_count=attempt_count,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )
        for quiz, question_count, attempt_count in rows
    ]

    return PublicUserProfileResponse(
        id=user.id,
        display_name=user.display_name,
        created_at=user.created_at,
        public_quiz_count=public_quiz_count,
        quizzes=quizzes,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )