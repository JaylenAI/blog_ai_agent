from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.post("/start")
async def start_pipeline() -> ApiResponse[dict]:
    return ApiResponse(
        success=False,
        error="파이프라인 미구현 (Phase 2에서 개발 예정)",
    )


@router.get("/runs/{run_id}")
async def get_run(run_id: int) -> ApiResponse[dict]:
    return ApiResponse(
        success=False,
        error="파이프라인 미구현 (Phase 2에서 개발 예정)",
    )
