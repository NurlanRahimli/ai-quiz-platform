import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


QUIZ_CREATED = "quiz_created"
QUIZ_UPDATED = "quiz_updated"
QUIZ_DELETED = "quiz_deleted"
QUIZ_COMPLETED = "quiz_completed"


def record_quiz_audit(
    db: Session,
    *,
    user_id: uuid.UUID,
    quiz_id: uuid.UUID,
    quiz_title: str,
    creator_name: str,
    action: str,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        quiz_id=quiz_id,
        quiz_title=quiz_title,
        creator_name=creator_name,
        action=action,
    )

    db.add(audit_log)

    return audit_log