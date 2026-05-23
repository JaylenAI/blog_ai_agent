import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.db.session import async_session_factory
from app.dependencies import create_pipeline_service, get_pipeline_service
from app.schemas.common import ApiResponse
from app.schemas.pipeline import (
    PipelineRunResponse,
    PipelineStartRequest,
    ValidationResponse,
    ValidationSummary,
)
from app.services.pipeline_service import PipelineService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

_SUCCESS_EVENT_TYPES = {"pipeline_complete", "gate_pending"}

_background_tasks: set[asyncio.Task] = set()


def _event_to_dict(event) -> dict:
    return {
        "event_type": event.event_type,
        "stage": event.stage,
        "message": event.message,
        "data": event.data,
    }


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
        data.article_id,
        auto_gate_one=data.auto_gate_one,
        format_id=data.format_id,
    ):
        if run_id is None and event.data.get("run_id") is not None:
            run_id = event.data["run_id"]
        events.append(_event_to_dict(event))

    return _collect_result(events, run_id=run_id)


@router.post("/runs/{run_id}/approve")
async def approve_gate(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    events = []
    async for event in service.resume_pipeline(run_id):
        events.append(_event_to_dict(event))

    return _collect_result(events)


@router.post("/runs/{run_id}/reject")
async def reject_gate(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    await service.reject_pipeline(run_id)
    return ApiResponse(success=True, data={"status": "cancelled"})


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: int,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[dict]:
    await service.cancel_run(run_id)
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


@router.get("/runs")
async def list_runs(
    article_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[list[PipelineRunResponse]]:
    if article_id is not None:
        runs = await service.get_runs_for_article(article_id)
    else:
        runs = await service.get_all_runs(limit=limit, offset=offset)
    return ApiResponse(
        success=True,
        data=[PipelineRunResponse.model_validate(r) for r in runs],
    )


@router.post("/runs/{run_id}/retry/stream")
async def retry_pipeline_stream(
    run_id: int,
) -> EventSourceResponse:
    queue: asyncio.Queue = asyncio.Queue()

    async def _retry_bg(q: asyncio.Queue, rid: int) -> None:
        async with async_session_factory() as session:
            try:
                svc = create_pipeline_service(session)
                async for event in svc.retry_pipeline(rid):
                    await q.put(_event_to_dict(event))
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("파이프라인 재시도 실패: %s", e, exc_info=True)
                await q.put({
                    "event_type": "pipeline_error",
                    "stage": "system",
                    "message": str(e),
                    "data": {},
                })
            finally:
                await q.put(None)

    task = asyncio.create_task(_retry_bg(queue, run_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return _sse_from_queue(queue)


@router.get("/runs/active")
async def get_active_run(
    service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[PipelineRunResponse | None]:
    run = await service.get_active_run()
    if not run:
        return ApiResponse(success=True, data=None)
    return ApiResponse(
        success=True,
        data=PipelineRunResponse.model_validate(run),
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


async def _run_pipeline_in_background(
    queue: asyncio.Queue,
    article_id: int,
    *,
    auto_gate_one: bool = False,
    format_id: str | None = None,
) -> None:
    async with async_session_factory() as session:
        try:
            service = create_pipeline_service(session)
            async for event in service.start_pipeline(
                article_id,
                auto_gate_one=auto_gate_one,
                format_id=format_id,
            ):
                await queue.put(_event_to_dict(event))
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("파이프라인 백그라운드 실행 실패: %s", e, exc_info=True)
            await queue.put({
                "event_type": "pipeline_error",
                "stage": "system",
                "message": str(e),
                "data": {},
            })
        finally:
            await queue.put(None)


async def _resume_pipeline_in_background(
    queue: asyncio.Queue,
    run_id: int,
) -> None:
    async with async_session_factory() as session:
        try:
            service = create_pipeline_service(session)
            async for event in service.resume_pipeline(run_id):
                await queue.put(_event_to_dict(event))
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("파이프라인 재개 실패: %s", e, exc_info=True)
            await queue.put({
                "event_type": "pipeline_error",
                "stage": "system",
                "message": str(e),
                "data": {},
            })
        finally:
            await queue.put(None)


def _sse_from_queue(queue: asyncio.Queue) -> EventSourceResponse:
    async def event_generator():
        try:
            while True:
                event_dict = await queue.get()
                if event_dict is None:
                    break
                yield {
                    "event": event_dict["event_type"],
                    "data": json.dumps(event_dict, ensure_ascii=False),
                }
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator())


@router.post("/start/stream")
async def start_pipeline_stream(
    data: PipelineStartRequest,
) -> EventSourceResponse:
    queue: asyncio.Queue = asyncio.Queue()

    task = asyncio.create_task(
        _run_pipeline_in_background(
            queue,
            data.article_id,
            auto_gate_one=data.auto_gate_one,
            format_id=data.format_id,
        )
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return _sse_from_queue(queue)


class ValidateOnlyRequest(BaseModel):
    article_id: int


@router.post("/validate-only/stream")
async def validate_only_stream(
    data: ValidateOnlyRequest,
) -> EventSourceResponse:
    article_id = data.article_id
    queue: asyncio.Queue = asyncio.Queue()

    async def _validate_bg(q: asyncio.Queue, aid: int) -> None:
        async with async_session_factory() as session:
            try:
                svc = create_pipeline_service(session)
                async for event in svc.validate_only(aid):
                    await q.put(_event_to_dict(event))
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("재검증 실패: %s", e, exc_info=True)
                await q.put({
                    "event_type": "pipeline_error",
                    "stage": "system",
                    "message": str(e),
                    "data": {},
                })
            finally:
                await q.put(None)

    task = asyncio.create_task(_validate_bg(queue, article_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return _sse_from_queue(queue)


@router.post("/runs/{run_id}/approve/stream")
async def approve_gate_stream(
    run_id: int,
) -> EventSourceResponse:
    queue: asyncio.Queue = asyncio.Queue()

    task = asyncio.create_task(
        _resume_pipeline_in_background(queue, run_id)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return _sse_from_queue(queue)
