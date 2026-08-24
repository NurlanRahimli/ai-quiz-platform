from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.ai import (
    CategorySuggestionResponse,
    QuizAIContext,
    TagSuggestionResponse,
)
from app.services.ai_service import (
    suggest_quiz_category,
    suggest_quiz_tags,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/suggest-category",
    response_model=CategorySuggestionResponse,
)
def suggest_category(
    quiz_context: QuizAIContext,
    current_user: User = Depends(get_current_user),
) -> CategorySuggestionResponse:
    try:
        return suggest_quiz_category(quiz_context)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate a category suggestion right now.",
        ) from exc


@router.post(
    "/suggest-tags",
    response_model=TagSuggestionResponse,
)
def suggest_tags(
    quiz_context: QuizAIContext,
    current_user: User = Depends(get_current_user),
) -> TagSuggestionResponse:
    try:
        return suggest_quiz_tags(quiz_context)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate tag suggestions right now.",
        ) from exc