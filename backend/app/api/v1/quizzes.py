import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.quiz_icons import DEFAULT_QUIZ_ICON
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate,
    QuizDetailResponse,
    QuizLandingResponse,
    QuizListResponse,
    QuizResponse,
    QuizDiscoveryResponse,
    QuizTakeResponse,
    QuizDiscoveryPageResponse,
    QuizDiscoveryOverviewResponse,
    QuizUpdate,
)
from app.models.question import Question
from app.schemas.ai import QuizIconContext
from app.services.ai_service import suggest_quiz_icon
from app.services.audit_service import (
    QUIZ_CREATED,
    QUIZ_DELETED,
    QUIZ_UPDATED,
    record_quiz_audit,
)

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
    icon = DEFAULT_QUIZ_ICON

    try:
        icon_suggestion = suggest_quiz_icon(
            QuizIconContext(
                title=quiz_data.title,
                description=quiz_data.description,
                category=quiz_data.category,
                tags=quiz_data.tags,
            )
        )
        icon = icon_suggestion.icon
    except Exception:
        # Icon selection is optional and must never block quiz creation.
        icon = DEFAULT_QUIZ_ICON

    quiz = Quiz(
        owner_id=current_user.id,
        title=quiz_data.title,
        description=quiz_data.description,
        visibility=quiz_data.visibility,
        category=quiz_data.category,
        tags=quiz_data.tags,
        icon=icon,
    )

    db.add(quiz)
    db.flush()

    record_quiz_audit(
        db,
        user_id=current_user.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        creator_name=current_user.display_name,
        action=QUIZ_CREATED,
    )

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
            icon=quiz.icon,
            creator_name=current_user.display_name,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )
        for quiz in quizzes
    ]


@router.get(
    "/discover",
    response_model=QuizDiscoveryPageResponse,
)
def discover_quizzes(
    search: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=100),
    sort: str = Query(
        default="popular",
        pattern="^(popular|newest|oldest)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizDiscoveryPageResponse:
    filters = [Quiz.visibility == "public"]

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        filters.append(
            Quiz.title.ilike(search_term)
            | Quiz.description.ilike(search_term)
            | User.display_name.ilike(search_term)
            | Quiz.category.ilike(search_term)
        )

    if category and category.strip():
        filters.append(
            func.lower(Quiz.category) == category.strip().lower()
        )

    total = db.scalar(
        select(func.count(Quiz.id))
        .join(User, User.id == Quiz.owner_id)
        .where(*filters)
    ) or 0

    attempt_count = func.count(func.distinct(QuizAttempt.id))

    if sort == "popular":
        order_by = (
            attempt_count.desc(),
            Quiz.created_at.desc(),
        )
    elif sort == "oldest":
        order_by = (Quiz.created_at.asc(),)
    else:
        order_by = (Quiz.created_at.desc(),)

    rows = db.execute(
        select(
            Quiz,
            User.display_name.label("creator_name"),
            func.count(func.distinct(Question.id)).label("question_count"),
            func.count(func.distinct(QuizAttempt.id)).label("attempt_count"),
        )
        .join(User, User.id == Quiz.owner_id)
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .outerjoin(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(*filters)
        .group_by(Quiz.id, User.display_name)
        .order_by(*order_by)
        .offset((page - 1) * page_size)
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
            icon=quiz.icon,
            creator_name=creator_name,
            question_count=question_count,
            attempt_count=attempt_count,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )
        for quiz, creator_name, question_count, attempt_count in rows
    ]

    total_pages = (total + page_size - 1) // page_size

    return QuizDiscoveryPageResponse(
        quizzes=quizzes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/discover/overview",
    response_model=QuizDiscoveryOverviewResponse,
)
def get_discovery_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizDiscoveryOverviewResponse:
    featured_rows = db.execute(
        select(
            Quiz,
            User.display_name.label("creator_name"),
            func.count(func.distinct(Question.id)).label("question_count"),
            func.count(func.distinct(QuizAttempt.id)).label("attempt_count"),
        )
        .join(User, User.id == Quiz.owner_id)
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .outerjoin(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(Quiz.visibility == "public")
        .group_by(Quiz.id, User.display_name)
        .order_by(
            func.count(func.distinct(QuizAttempt.id)).desc(),
            Quiz.created_at.desc(),
        )
        .limit(4)
    ).all()

    featured = [
        QuizDiscoveryResponse(
            id=quiz.id,
            owner_id=quiz.owner_id,
            title=quiz.title,
            description=quiz.description,
            visibility=quiz.visibility,
            category=quiz.category,
            tags=quiz.tags,
            icon=quiz.icon,
            creator_name=creator_name,
            question_count=question_count,
            attempt_count=attempt_count,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
        )
        for quiz, creator_name, question_count, attempt_count in featured_rows
    ]

    categories = list(
        db.scalars(
            select(Quiz.category)
            .where(
                Quiz.visibility == "public",
                Quiz.category.is_not(None),
            )
            .distinct()
            .order_by(Quiz.category)
        )
    )

    return QuizDiscoveryOverviewResponse(
        featured=featured,
        categories=categories,
    )


@router.get(
    "/{quiz_id}/take",
    response_model=QuizTakeResponse,
)
def take_quiz(
    quiz_id: uuid.UUID,
    db: Session = Depends(get_db),
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
        icon=quiz.icon,
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


    record_quiz_audit(
        db,
        user_id=current_user.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        creator_name=current_user.display_name,
        action=QUIZ_UPDATED,
    )

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

    record_quiz_audit(
        db,
        user_id=current_user.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        creator_name=current_user.display_name,
        action=QUIZ_DELETED,
    )

    db.delete(quiz)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)