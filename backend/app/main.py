"""
KEGGPathRank — FastAPI Application Entry Point.

This module creates and configures the FastAPI application, including:
- CORS middleware for frontend communication
- Global exception handling
- Service initialization on startup
- API route registration
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import configure_logging, CORS_ORIGINS, CACHE_DIR
from app.api.routes import router, init_services
from app.services.kegg_service import KEGGService
from app.utils.validators import ValidationError

# Configure logging before anything else
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize services on startup."""
    logger.info("KEGGPathRank starting up...")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    kegg_service = KEGGService()
    init_services(kegg_service)
    logger.info("All services initialized. Application ready.")
    yield
    logger.info("KEGGPathRank shutting down.")


app = FastAPI(
    title="KEGGPathRank API",
    description=(
        "A Python-based system for ranking biologically relevant KEGG pathways "
        "from gene sets. Performs gene validation, pathway mapping, statistical "
        "enrichment analysis (Fisher's exact test), FDR correction, and "
        "deterministic pathway ranking."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ───────────────────────────────────────────────

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors with structured JSON responses."""
    logger.warning("Validation error: %s", exc.message)
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions — never expose raw tracebacks to clients."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected internal error occurred. Please try again later.",
            "details": None,
        },
    )


# ── Register Routes ─────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")


# ── Root Endpoint ────────────────────────────────────────────────────────────

@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint — basic application information."""
    return {
        "application": "KEGGPathRank",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
