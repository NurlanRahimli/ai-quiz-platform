from pathlib import Path

from fastapi import UploadFile

from app.core.quiz_import import (
    ALLOWED_QUIZ_IMPORT_CONTENT_TYPES,
    ALLOWED_QUIZ_IMPORT_EXTENSIONS,
    MAX_QUIZ_IMPORT_FILE_SIZE,
)


class QuizImportValidationError(Exception):
    pass


def _has_valid_file_signature(
    contents: bytes,
    content_type: str | None,
) -> bool:
    if content_type == "application/pdf":
        return contents.startswith(b"%PDF-")

    if content_type == "image/jpeg":
        return contents.startswith(b"\xff\xd8\xff")

    if content_type == "image/png":
        return contents.startswith(b"\x89PNG\r\n\x1a\n")

    return False


async def validate_quiz_import_file(
    file: UploadFile,
) -> bytes:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_QUIZ_IMPORT_EXTENSIONS:
        raise QuizImportValidationError(
            "Please upload a PDF, JPG, JPEG, or PNG file."
        )

    if file.content_type not in ALLOWED_QUIZ_IMPORT_CONTENT_TYPES:
        raise QuizImportValidationError(
            "Please upload a valid PDF, JPG, JPEG, or PNG file."
        )

    contents = await file.read()

    if not contents:
        raise QuizImportValidationError(
            "The uploaded file is empty."
        )

    if len(contents) > MAX_QUIZ_IMPORT_FILE_SIZE:
        raise QuizImportValidationError(
            "The uploaded file must be 10 MB or smaller."
        )

    if not _has_valid_file_signature(
        contents,
        file.content_type,
    ):
        raise QuizImportValidationError(
            "The uploaded file does not appear to be a valid PDF, JPG, JPEG, or PNG file."
        )

    return contents


