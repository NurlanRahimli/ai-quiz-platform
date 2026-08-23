import uuid

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    quiz_id: uuid.UUID | None
    action: str
    quiz_title: str
    creator_name: str
    created_at: datetime


class AuditLogPageResponse(BaseModel):
    audit_logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int