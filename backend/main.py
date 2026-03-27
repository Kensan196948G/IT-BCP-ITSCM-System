"""IT-BCP-ITSCM-System Backend API"""

import json
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.monitoring import metrics_collector
from apps.routers import (
    bia,
    contacts,
    dashboard,
    exercises,
    incidents,
    monitoring,
    notifications,
    procedures,
    runbook,
    scenarios,
    systems,
    ws,
)
from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting IT-BCP-ITSCM-System API v%s", settings.APP_VERSION)
    logger.info(
        "Database URL: %s",
        settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "N/A",
    )
    yield
    logger.info("Shutting down IT-BCP-ITSCM-System API")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

tags_metadata = [
    {
        "name": "systems",
        "description": "ITシステムBCP登録・管理。RTO/RPO目標値、代替手段、DR試験結果を管理します。",
    },
    {
        "name": "exercises",
        "description": "BCP訓練・演習の計画・実施・結果管理。Tabletop/Functional/Full-scale演習に対応。",
    },
    {
        "name": "incidents",
        "description": (
            "アクティブBCPインシデントの追跡・管理。RTO進捗のリアルタイム監視、"
            "タスク管理、状況報告、戦況室ダッシュボードを含みます。"
        ),
    },
    {
        "name": "dashboard",
        "description": "BCP準備状況ダッシュボード。全システムのRTO状況と準備スコアを提供します。",
    },
    {
        "name": "recovery-procedures",
        "description": "復旧手順書の管理。シナリオ別の復旧手順、優先順位、レビューサイクルを管理します。",
    },
    {
        "name": "contacts",
        "description": "緊急連絡先・ベンダー連絡先の管理。エスカレーション体制とSLA情報を含みます。",
    },
    {
        "name": "bia",
        "description": "ビジネスインパクト分析(BIA)。リスクスコア算出、財務影響評価、リスクマトリクスを提供します。",
    },
    {
        "name": "scenarios",
        "description": "BCPシナリオ管理。テーブルトップ演習用のシナリオテンプレートとインジェクションを管理します。",
    },
    {
        "name": "notifications",
        "description": "通知連携・エスカレーション自動化。Teams/Email通知送信、エスカレーション計画・発動・状況追跡を管理します。",
    },
    {
        "name": "monitoring",
        "description": "監視・メトリクス・ヘルスプローブ。Prometheusフォーマットメトリクス、Kubernetes互換プローブを提供します。",
    },
    {
        "name": "runbook",
        "description": "運用ランブック。デプロイチェックリスト、ロールバック手順、DRフェイルオーバー、インシデント対応プレイブックを提供します。",
    },
]

app = FastAPI(
    title="IT-BCP-ITSCM-System API",
    description=(
        "ISO20000/ISO27001/NIST CSF準拠のIT事業継続計画(BCP)・ITサービス継続管理(ITSCM) API。\n\n"
        "主な機能:\n"
        "- ITシステムのRTO/RPO目標管理\n"
        "- BCP訓練・演習の計画と結果管理\n"
        "- アクティブインシデントのリアルタイム追跡\n"
        "- BCP準備状況ダッシュボード"
    ),
    version="0.1.0",
    docs_url="/docs",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# CORS middleware (uses config values)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next: object) -> JSONResponse:
    """Attach security headers to every response."""
    response = await call_next(request)  # type: ignore[operator]
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: object) -> JSONResponse:
    """Log method, path, status code and processing time."""
    start = time.time()
    response = await call_next(request)  # type: ignore[operator]
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: object) -> JSONResponse:
    """Record request metrics for monitoring."""
    start = time.time()
    response = await call_next(request)  # type: ignore[operator]
    duration = time.time() - start
    metrics_collector.record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )
    return response


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 with detailed validation errors."""
    # Sanitise errors so they are always JSON-serialisable
    errors = json.loads(json.dumps(exc.errors(), default=str))
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "message": "Validation error",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Forward HTTP exceptions as-is."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler. Hide details in production."""
    logger.exception("Unhandled exception: %s", exc)
    detail = str(exc) if settings.ENVIRONMENT != "production" else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(systems.router)
app.include_router(exercises.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)
app.include_router(procedures.router)
app.include_router(contacts.router)
app.include_router(bia.router)
app.include_router(scenarios.router)
app.include_router(notifications.router)
app.include_router(monitoring.router)
app.include_router(runbook.router)
app.include_router(ws.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint with DB connectivity, environment and version."""
    db_ok = True
    try:
        from database import engine

        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_ok else "disconnected",
    }
