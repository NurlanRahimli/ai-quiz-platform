from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.chatbot import (
    ChatbotMessageRequest,
    ChatbotQueryResponse,
    ChatbotReportResponse,
)
from app.services.chatbot_service import answer_chatbot_data_question
from app.services.chatbot_response_service import (
    format_chatbot_query_result,
)


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)


@router.post(
    "",
    response_model=ChatbotQueryResponse | ChatbotReportResponse,
)
def ask_chatbot(
    payload: ChatbotMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatbotQueryResponse | ChatbotReportResponse:
    current_date = datetime.now(timezone.utc).date().isoformat()

    result = answer_chatbot_data_question(
        db,
        user_id=current_user.id,
        question=payload.message,
        current_date=current_date,
    )

    if isinstance(
        result,
        (ChatbotQueryResponse, ChatbotReportResponse),
    ):
        return result

    return format_chatbot_query_result(result)
