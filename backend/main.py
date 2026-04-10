"""
FastAPI Application Entry Point
Image Caption Generator — Production Backend
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.services.cache import cache_service
from app.services.model_service import model_service

# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup; clean up on shutdown."""
    setup_logging()
    logger = get_logger("startup")

    logger.info("Starting Image Caption Generator API...")
    await cache_service.connect()

    # Lazy-load model (fast startup; loads on first request if not pre-loaded)
    # To pre-load on startup (recommended for production), uncomment:
    # model_service.load()
    logger.info("API startup complete.")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await cache_service.disconnect()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
settings = get_settings()
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Production-grade Image Caption Generator using CNN + LSTM with Attention",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware — request logging
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    logger.info(
        "HTTP",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        ms=round(elapsed),
    )
    return response


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception",
                 path=request.url.path,
                 error=str(exc),
                 exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Image Caption Generator API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
