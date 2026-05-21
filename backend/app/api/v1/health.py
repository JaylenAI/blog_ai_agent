from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> ApiResponse[dict]:
    return ApiResponse(
        success=True,
        data={
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "0.1.0",
        },
    )
