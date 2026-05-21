from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        logger.warning("ValueError: %s | path=%s", exc, request.url.path)
        return JSONResponse(
            status_code=400,
            content=ApiResponse(success=False, error=str(exc)).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled error: %s | path=%s", exc, request.url.path, exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=False, error="Internal server error"
            ).model_dump(),
        )
