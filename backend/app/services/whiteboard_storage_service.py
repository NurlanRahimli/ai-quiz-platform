import base64
import binascii
import uuid
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

from app.core.config import settings


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

    if not settings.cloudinary_url:
        raise RuntimeError(
            "Cloudinary is not configured"
        )

    parsed_url = urlparse(settings.cloudinary_url)

    if (
        parsed_url.scheme != "cloudinary"
        or not parsed_url.hostname
        or not parsed_url.username
        or not parsed_url.password
    ):
        raise RuntimeError(
            "CLOUDINARY_URL is invalid"
        )

    cloudinary.config(
        cloud_name=parsed_url.hostname,
        api_key=parsed_url.username,
        api_secret=parsed_url.password,
        secure=True,
    )

    public_id = f"{attempt_id}_{question_id}"

    result = cloudinary.uploader.upload(
        image_data,
        folder="quiz-app/whiteboards",
        public_id=public_id,
        resource_type="image",
        overwrite=True,
    )

    secure_url = result.get("secure_url")

    if not secure_url:
        raise RuntimeError(
            "Cloudinary did not return a secure image URL"
        )

    return secure_url
