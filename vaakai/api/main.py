"""VaakAI — FastAPI Application Factory.

Main entry point for the VaakAI API server.
Initializes all subsystems, registers routes, and handles graceful shutdown.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from config import settings
from core.orchestrator import orchestrator
from memory.postgres_client import init_db
from compliance.pii_redactor import pii_redactor

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup & shutdown hooks."""
    logger.info("vaakai_starting", version="1.0.0")

    # Initialize database tables (skip if DB unavailable in dev)
    try:
        await init_db()
    except Exception as e:
        logger.warning("db_init_skipped", error=str(e))

    # Initialize orchestrator (initializes all sub-components)
    await orchestrator.initialize()

    # Initialize compliance modules
    await pii_redactor.initialize()

    logger.info("vaakai_ready", port=settings.app_port)
    yield

    # Shutdown
    logger.info("vaakai_shutting_down")
    await orchestrator.shutdown()
    logger.info("vaakai_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VaakAI",
        description="Multilingual AI Voice Chatbot — Real-Time Customer Assistance",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_latency_header(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Response-Time-Ms"] = str(latency_ms)
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    # Register routers
    from api.call import router as call_router
    from api.crm import router as crm_router
    from api.analytics import router as analytics_router
    from api.admin import router as admin_router

    app.include_router(call_router, prefix="/api/v1", tags=["Call"])
    app.include_router(crm_router, prefix="/api/v1", tags=["CRM"])
    app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
    app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])

    # Health check
    @app.get("/api/v1/health", tags=["System"])
    async def health():
        return {
            "status": "healthy",
            "service": "vaakai",
            "version": "1.0.0",
            "active_sessions": len(orchestrator.get_active_sessions()),
        }

    return app


app = create_app()
