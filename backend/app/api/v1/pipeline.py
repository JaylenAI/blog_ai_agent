import json

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_pipeline_service
from app.schemas.common import ApiResponse
from app.schemas.pipeline import (
    PipelineRunResponse,
    PipelineStartRequest,
    ValidationResponse,
    ValidationSummary,
)
from app.services.pipeline_service import PipelineService

router = APIRouter()

_SUCCESS_EVENT_TYPES = {"pipeline_complete", "gate_pending"}


def _collect_result(
    events: list[dict], *, run_id: int | None = None
) -> ApiResponse[dict]:
    last = events[-1] if events else {}
    success = last.get("event_type") in _SUCCESS_EVENT_TYPES
    data: dict = {"events": events}
    if run_id is not None:
        data["run_id"] = run_id
    return ApiResponse(
        success=success,
        data=data,
        error=last.get("message") if not success else None,
    )


@router.post("/start")
async def start_pipeline(
    data: PipelineStartRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    events = []
    run_id: int | None = None
    async for event in service.start_pipeline(
        data.article_id, auto_gate_one=data.auto_gate_one
    ):
        if run_id is None and event.data.get("run_id") is not None:
            run_id = event.data["run_id"]
        events.append({
            "event_type": event.event_type,
            "stage": event.stage,
            "message": event.message,
            "data": event.data,
        })

    return _collect_result(events, run_id=run_id)


@router.post("/runs/{run_id}/approve")
async def approve_gate(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    events = []
    async for event in service.resume_pipeline(run_id):
        events.append({
            "event_type": event.event_type,
            "stage": event.stage,
            "message": event.message,
            "data": event.data,
        })

    return _collect_result(events)


@router.post("/runs/{run_id}/reject")
async def reject_gate(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    try:
        await service.reject_pipeline(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApiResponse(success=True, data={"status": "cancelled"})


@router.get("/runs/{run_id}/validations")
async def get_validations(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    validations = await service.get_validations(run_id)
    items = [ValidationResponse.model_validate(v) for v in validations]

    total = len(items)
    passed = sum(1 for v in items if v.passed)

    by_category: dict[str, dict[str, int]] = {}
    for v in items:
        cat = v.category.value
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if v.passed:
            by_category[cat]["passed"] += 1

    summary = ValidationSummary(
        total=total,
        passed=passed,
        failed=total - passed,
        score=round(passed / total, 2) if total > 0 else 0.0,
        by_category=by_category,
    )

    return ApiResponse(
        success=True,
        data={
            "validations": [v.model_dump() for v in items],
            "summary": summary.model_dump(),
        },
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


@router.post("/start/stream")
async def start_pipeline_stream(
    data: PipelineStartRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> EventSourceResponse:
    async def event_generator():
        async for event in service.start_pipeline(
            data.article_id, auto_gate_one=data.auto_gate_one
        ):
            yield {
                "event": event.event_type,
                "data": json.dumps({
                    "event_type": event.event_type,
                    "stage": event.stage,
                    "message": event.message,
                    "data": event.data,
                }, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


@router.post("/runs/{run_id}/approve/stream")
async def approve_gate_stream(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> EventSourceResponse:
    async def event_generator():
        async for event in service.resume_pipeline(run_id):
            yield {
                "event": event.event_type,
                "data": json.dumps({
                    "event_type": event.event_type,
                    "stage": event.stage,
                    "message": event.message,
                    "data": event.data,
                }, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
