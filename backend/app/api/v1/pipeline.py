
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_pipeline_service
from app.schemas.common import ApiResponse
from app.schemas.pipeline import PipelineRunResponse, PipelineStartRequest
from app.services.pipeline_service import PipelineService

router = APIRouter()


@router.post("/start")
async def start_pipeline(
    data: PipelineStartRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    events = []
    async for event in service.start_pipeline(data.article_id):
        events.append({
            "event_type": event.event_type,
            "stage": event.stage,
            "message": event.message,
            "data": event.data,
        })

    last = events[-1] if events else {}
    success = last.get("event_type") == "pipeline_complete"

    return ApiResponse(
        success=success,
        data={"events": events},
        error=last.get("message") if not success else None,
    )


@router.get("/runs/{run_id}")
async def get_run(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[PipelineRunResponse]:
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return ApiResponse(
        success=True,
        data=PipelineRunResponse.model_validate(run),
    )
