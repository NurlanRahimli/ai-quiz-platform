from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timezone

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogPageResponse,
    AuditLogResponse,
)

ALLOWED_AUDIT_ACTIONS = {
    "quiz_created",
    "quiz_updated",
    "quiz_deleted",
    "quiz_completed",
}

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=AuditLogPageResponse,
)
def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogPageResponse:

    if action is not None and action not in ALLOWED_AUDIT_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid audit action",
        )

    filters = [
        AuditLog.user_id == current_user.id,
    ]

    if action is not None:
        filters.append(AuditLog.action == action)

    if search is not None:
        search_term = search.strip()

        if search_term:
            filters.append(
                or_(
                    AuditLog.quiz_title.ilike(f"%{search_term}%"),
                    AuditLog.creator_name.ilike(f"%{search_term}%"),
                )
            )

    if search is not None:
        search = search.strip()

        if search:
            search_pattern = f"%{search}%"

            filters.append(
                or_(
                    AuditLog.quiz_title.ilike(search_pattern),
                    AuditLog.creator_name.ilike(search_pattern),
                )
            )

    
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from cannot be after date_to",
        )

    if date_from is not None:
        start_datetime = datetime.combine(
            date_from,
            time.min,
            tzinfo=timezone.utc,
        )

        filters.append(
            AuditLog.created_at >= start_datetime
        )

    if date_to is not None:
        end_datetime = datetime.combine(
            date_to,
            time.max,
            tzinfo=timezone.utc,
        )

        filters.append(
            AuditLog.created_at <= end_datetime
        )


    if date_from is not None and date_to is not None:
        if date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="date_from cannot be after date_to",
            )

    if date_from is not None:
        filters.append(
            AuditLog.created_at >= datetime.combine(
                date_from,
                time.min,
            )
        )

    if date_to is not None:
        filters.append(
            AuditLog.created_at <= datetime.combine(
                date_to,
                time.max,
            )
        )


    total = db.scalar(
        select(func.count(AuditLog.id)).where(*filters)
    ) or 0

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    rows = list(
        db.scalars(
            select(AuditLog)
            .where(*filters)
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )

    return AuditLogPageResponse(
        audit_logs=[
            AuditLogResponse.model_validate(row)
            for row in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )