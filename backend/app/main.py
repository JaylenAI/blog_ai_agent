import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import register_error_handlers
from app.api.middleware.rate_limiter import RateLimiterMiddleware
from app.api.middleware.request_logger import RequestLoggerMiddleware
from app.api.router import api_router
from app.config import settings
from app.db.engine import init_db
from app.formats import get_format_registry
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

_shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await init_db()
    registry = get_format_registry()
    logger.info(
        "Blog AI Agent 시작 (port=%d, formats=%d)",
        settings.backend_port,
        len(registry.format_ids),
    )
    yield
    logger.info("Blog AI Agent 종료")
    _shutdown_event.set()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Blog AI Agent",
        description="AI 기반 블로그 자동화 플랫폼",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RateLimiterMiddleware, limit=60, window=60)
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{settings.frontend_port}",
            f"http://127.0.0.1:{settings.frontend_port}",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
