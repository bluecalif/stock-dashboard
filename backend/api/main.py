"""FastAPI application — entry point, CORS, error handlers."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import (
    analysis,
    assets,
    auth,
    chat,
    correlation,
    dashboard,
    factors,
    fx,
    health,
    prices,
    profile,
    signals,
    simulation,
)
from config.settings import settings

# OS environ에 .env 로드 — LangSmith 등 라이브러리가 os.getenv()로 직접 참조
load_dotenv()

# 앱 로거 레벨 설정 — LOG_LEVEL 환경변수 또는 기본 INFO
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup / shutdown hooks."""
    logger.info("Stock Dashboard API starting up")

    # 캐시 프리페치 — 백그라운드로 실행 (서버 시작 블로킹 없음)
    from api.services.llm.agentic.cache_warmup import warmup_cache

    asyncio.create_task(warmup_cache())

    yield
    logger.info("Stock Dashboard API shutting down")


app = FastAPI(
    title="Stock Dashboard API",
    version="0.1.0",
    lifespan=lifespan,
)

# --- CORS ---
# localhost 모든 포트 허용 (Vite가 5173, 5174, ... 동적 할당)
_origins: list[str] = []
if settings.cors_origins:
    _origins.extend(
        o.strip().rstrip("/") for o in settings.cors_origins.split(",") if o.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Error handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 with structured error details."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": str(exc),
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions → 500."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        },
    )


# --- Routers ---
app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(prices.router)
app.include_router(factors.router)
app.include_router(signals.router)
app.include_router(dashboard.router)
app.include_router(correlation.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(simulation.router)
app.include_router(fx.router)
