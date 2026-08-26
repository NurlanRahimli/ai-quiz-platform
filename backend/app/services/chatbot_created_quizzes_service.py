import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.quiz import Quiz


def _apply_created_quiz_filters(
    query,
    *,
    user_id: uuid.UUID,
    visibility: str | None = None,
    category: str | None = None,
    title_search: str | None = None,
):
    query = query.where(
        Quiz.owner_id == user_id
    )

    if visibility is not None:
        query = query.where(
            Quiz.visibility == visibility
        )

    if category is not None:
        query = query.where(
            func.lower(Quiz.category) == category.strip().lower()
        )

    if title_search is not None:
        cleaned_title = title_search.strip()

        if cleaned_title:
            query = query.where(
                Quiz.title.ilike(
                    f"%{cleaned_title}%"
                )
            )

    return query


def count_user_created_quizzes(
    db: Session,
    *,
    user_id: uuid.UUID,
    visibility: str | None = None,
    category: str | None = None,
    title_search: str | None = None,
) -> int:
    query = select(
        func.count(Quiz.id)
    )

    query = _apply_created_quiz_filters(
        query,
        user_id=user_id,
        visibility=visibility,
        category=category,
        title_search=title_search,
    )

    count = db.scalar(query)

    return int(count or 0)


def list_user_created_quizzes(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 10,
    visibility: str | None = None,
    category: str | None = None,
    title_search: str | None = None,
    sort_direction: str = "desc",
) -> list[Quiz]:
    safe_limit = min(
        max(limit, 1),
        50,
    )

    query = select(Quiz)

    query = _apply_created_quiz_filters(
        query,
        user_id=user_id,
        visibility=visibility,
        category=category,
        title_search=title_search,
    )

    if sort_direction == "asc":
        query = query.order_by(
            Quiz.created_at.asc()
        )
    else:
        query = query.order_by(
            Quiz.created_at.desc()
        )

    query = query.limit(safe_limit)

    return list(
        db.scalars(query).all()
    )
