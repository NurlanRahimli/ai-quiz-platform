from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.ai import (
    CategorySuggestionResponse,
    ImportedQuiz,
    QuizAIContext,
    TagSuggestionResponse,
)
from app.services.ai_service import (
    QuizImportQuestionLimitError,
    extract_quiz_from_file,
    suggest_quiz_category,
    suggest_quiz_tags,
)
from app.services.quiz_import_service import (
    QuizImportValidationError,
    validate_quiz_import_file,
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


@router.post(
    "/import-quiz",
    response_model=ImportedQuiz,
    status_code=status.HTTP_200_OK,
)
async def import_quiz(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> ImportedQuiz:
    try:
        contents = await validate_quiz_import_file(file)

        return extract_quiz_from_file(
            contents=contents,
            content_type=file.content_type or "",
        )

    except QuizImportValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except QuizImportQuestionLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to import the quiz right now.",
        ) from exc