"""IT-BCP-ITSCM-System Backend API"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.routers import dashboard, exercises, incidents, systems
from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting IT-BCP-ITSCM-System API v%s", settings.APP_VERSION)
    logger.info("Database URL: %s", settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "N/A")
    yield
    logger.info("Shutting down IT-BCP-ITSCM-System API")


app = FastAPI(
    title=settings.APP_NAME,
    description="IT事業継続管理システム API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(systems.router)
app.include_router(exercises.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint with basic status info."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
    }
