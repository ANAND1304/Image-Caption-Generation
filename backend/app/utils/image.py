"""
Image validation helpers — size, format, and content checks.
"""

import io
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


async def validate_and_load_image(file: UploadFile) -> tuple[Image.Image, bytes]:
    """
    Validate an uploaded image file.
    Returns: (PIL Image, raw bytes)
    Raises: HTTPException on validation failure.
    """
    # 1. Content-type check
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed: {', '.join(settings.allowed_content_types)}"
            ),
        )

    # 2. Read bytes
    image_bytes = await file.read()

    # 3. Size check
    if len(image_bytes) > settings.max_image_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File too large ({len(image_bytes) // 1024}KB). "
                f"Maximum allowed: {settings.max_image_size_mb}MB."
            ),
        )

    # 4. Empty file check
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 5. Parse with PIL
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not decode image. Please upload a valid image file.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image processing error: {str(e)}",
        )

    # 6. Minimum dimensions
    w, h = image.size
    if w < 10 or h < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image too small ({w}x{h}px). Minimum: 10x10px.",
        )

    return image, image_bytes
