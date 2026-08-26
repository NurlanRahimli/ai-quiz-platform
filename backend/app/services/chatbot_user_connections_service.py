import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_follow import UserFollow


def count_user_connections(
    db: Session,
    *,
    user_id: uuid.UUID,
    direction: str,
) -> int:
    if direction == "followers":
        query = (
            select(func.count(UserFollow.follower_id))
            .where(
                UserFollow.following_id == user_id
            )
        )
    elif direction == "following":
        query = (
            select(func.count(UserFollow.following_id))
            .where(
                UserFollow.follower_id == user_id
            )
        )
    else:
        raise ValueError(
            f"Unsupported user connection direction: {direction}"
        )

    count = db.scalar(query)

    return int(count or 0)


def list_user_connections(
    db: Session,
    *,
    user_id: uuid.UUID,
    direction: str,
    limit: int = 10,
) -> list[User]:
    safe_limit = min(
        max(limit, 1),
        50,
    )

    if direction == "followers":
        query = (
            select(User)
            .join(
                UserFollow,
                User.id == UserFollow.follower_id,
            )
            .where(
                UserFollow.following_id == user_id,
                User.is_active.is_(True),
            )
            .order_by(UserFollow.created_at.desc())
            .limit(safe_limit)
        )
    elif direction == "following":
        query = (
            select(User)
            .join(
                UserFollow,
                User.id == UserFollow.following_id,
            )
            .where(
                UserFollow.follower_id == user_id,
                User.is_active.is_(True),
            )
            .order_by(UserFollow.created_at.desc())
            .limit(safe_limit)
        )
    else:
        raise ValueError(
            f"Unsupported user connection direction: {direction}"
        )

    return list(
        db.scalars(query).all()
    )
