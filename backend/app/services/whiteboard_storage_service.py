import base64
import binascii
import uuid
from pathlib import Path


WHITEBOARD_UPLOAD_DIR = Path("uploads/whiteboards")
PNG_DATA_URL_PREFIX = "data:image/png;base64,"
MAX_WHITEBOARD_IMAGE_SIZE = 5 * 1024 * 1024


class WhiteboardImageValidationError(ValueError):
    pass


def save_whiteboard_image(
    image_data: str,
    *,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
) -> str:
    if not image_data.startswith(PNG_DATA_URL_PREFIX):
        raise WhiteboardImageValidationError(
            "Whiteboard image must be a PNG image."
        )

    encoded_image = image_data[len(PNG_DATA_URL_PREFIX):]

    try:
        image_bytes = base64.b64decode(
            encoded_image,
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise WhiteboardImageValidationError(
            "Whiteboard image contains invalid image data."
        ) from exc

    if not image_bytes:
        raise WhiteboardImageValidationError(
            "Whiteboard image cannot be empty."
        )

    if len(image_bytes) > MAX_WHITEBOARD_IMAGE_SIZE:
        raise WhiteboardImageValidationError(
            "Whiteboard image must be 5 MB or smaller."
        )

    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise WhiteboardImageValidationError(
            "Whiteboard image must contain valid PNG data."
        )

    WHITEBOARD_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{attempt_id}_{question_id}.png"
    file_path = WHITEBOARD_UPLOAD_DIR / filename

    file_path.write_bytes(image_bytes)

    return f"/uploads/whiteboards/{filename}"