"""
API routes for the Image Caption Generator.
"""

from fastapi import APIRouter, File, UploadFile, Depends, Query
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.cache import cache_service
from app.services.model_service import model_service
from app.utils.image import validate_and_load_image

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["captions"])


@router.post("/generate-caption")
async def generate_caption(
    file: UploadFile = File(..., description="Image file (JPEG/PNG/WEBP)"),
    beam_size: int = Query(
        default=3,
        ge=1, le=5,
        description="Beam search width (higher = better but slower)",
    ),
):
    """
    Generate a natural language caption for the uploaded image using BLIP AI.
    """
    # Validate image
    image, image_bytes = await validate_and_load_image(file)

    # Check cache first
    cached = await cache_service.get(image_bytes, beam_size)
    if cached:
        cached["cached"] = True
        return JSONResponse(content=cached)

    # Run inference
    result = model_service.generate_caption(image, beam_size=beam_size)
    result["cached"] = False

    # Store in cache
    await cache_service.set(image_bytes, beam_size, result)

    logger.info("Caption request completed",
                filename=file.filename,
                caption=result["caption"],
                ms=result["processing_time_ms"],
                mode=result.get("model_mode", "unknown"))

    return JSONResponse(content=result)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "model_loaded": model_service.is_loaded,
        "model_mode": model_service.mode,    # "blip" | "custom" | "mock"
        "redis_connected": cache_service.is_connected,
        "device": model_service.device_name,
    }


@router.get("/config")
async def get_config():
    """Public config for the frontend."""
    return {
        "max_image_size_mb": settings.max_image_size_mb,
        "allowed_types": settings.allowed_content_types,
        "max_beam_size": 5,
        "default_beam_size": settings.beam_size,
        "model_mode": model_service.mode,
    }
