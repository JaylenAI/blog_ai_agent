import asyncio
import contextlib
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.pipeline_run import PipelineRun, PipelineStage, PipelineStatus
from app.pipeline.base import PipelineEvent, Stage, StageInput
from app.services.webhook_service import dispatch_webhook
from app.utils.logger import get_logger

logger = get_logger(__name__)


STAGE_TIMEOUTS: dict[str, str] = {
    "router": "router_timeout",
    "researcher": "researcher_timeout",
    "outliner": "outliner_timeout",
    "generator": "generator_timeout",
    "validator": "validator_timeout",
    "publisher": "publisher_timeout",
}


class PipelineOrchestrator:
    def __init__(self, stages: list[Stage]) -> None:
        self._stages = stages

    def _get_timeout(self, stage_name: str) -> int:
        attr = STAGE_TIMEOUTS.get(stage_name)
        if attr:
            return getattr(settings, attr, settings.stage_timeout)
        return settings.stage_timeout

    async def execute(
        self,
        pipeline_run: PipelineRun,
        topic: str,
        slug: str,
        *,
        format_id: str = "concept",
        session: AsyncSession,
    ) -> AsyncGenerator[PipelineEvent, None]:
        pipeline_run.status = PipelineStatus.RUNNING
        pipeline_run.started_at = datetime.now(UTC)
        await session.commit()

        stage_input = StageInput(
            article_id=pipeline_run.article_id,
            slug=slug,
            topic=topic,
            format_id=format_id,
        )

        durations: dict[str, float] = dict(pipeline_run.stage_durations or {})
        first = True
        for stage in self._stages:
            pipeline_run.current_stage = PipelineStage(stage.name)
            await session.commit()

            start_data: dict = {}
            if first:
                start_data["run_id"] = pipeline_run.id
                first = False

            yield PipelineEvent(
                event_type="stage_start",
                stage=stage.name,
                message=f"{stage.name} 스테이지 시작",
                data=start_data,
            )

            stage_start = datetime.now(UTC)
            timeout = self._get_timeout(stage.name)
            try:
                progress_queue: asyncio.Queue[PipelineEvent] = asyncio.Queue()
                task = asyncio.create_task(
                    stage.execute(
                        stage_input,
                        on_progress=lambda evt, _q=progress_queue: _q.put_nowait(evt),
                    )
                )

                deadline = asyncio.get_event_loop().time() + timeout
                while not task.done():
                    remaining = deadline - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task
                        raise TimeoutError(
                            f"Stage {stage.name} 타임아웃 ({timeout}초)"
                        )
                    try:
                        evt = await asyncio.wait_for(
                            progress_queue.get(), timeout=min(0.5, remaining)
                        )
                        yield evt
                    except TimeoutError:
                        continue

                while not progress_queue.empty():
                    yield progress_queue.get_nowait()

                output = task.result()
            except Exception as e:
                elapsed = (datetime.now(UTC) - stage_start).total_seconds()
                durations[stage.name] = elapsed
                pipeline_run.stage_durations = durations
                logger.error("Stage %s 실패: %s", stage.name, e, exc_info=True)
                pipeline_run.status = PipelineStatus.FAILED
                pipeline_run.error_message = str(e)
                await session.commit()

                error_event = PipelineEvent(
                    event_type="stage_error",
                    stage=stage.name,
                    message=str(e),
                )
                yield error_event
                await dispatch_webhook("pipeline_error", {
                    "run_id": pipeline_run.id,
                    "article_id": pipeline_run.article_id,
                    "stage": stage.name,
                    "error": str(e),
                })
                return

            elapsed = (datetime.now(UTC) - stage_start).total_seconds()
            durations[stage.name] = round(elapsed, 2)
            pipeline_run.stage_durations = durations

            if not output.success:
                pipeline_run.status = PipelineStatus.FAILED
                pipeline_run.error_message = output.error
                await session.commit()

                yield PipelineEvent(
                    event_type="stage_error",
                    stage=stage.name,
                    message=output.error,
                )
                return

            if output.data.get("gate_pending"):
                pipeline_run.status = PipelineStatus.PAUSED
                await session.commit()

                gate_event = PipelineEvent(
                    event_type="gate_pending",
                    stage=stage.name,
                    message=f"{stage.name} 사용자 검수 대기",
                    data=output.data,
                )
                yield gate_event
                await dispatch_webhook("gate_pending", {
                    "run_id": pipeline_run.id,
                    "article_id": pipeline_run.article_id,
                    "stage": stage.name,
                })
                return

            stage_input = StageInput(
                article_id=pipeline_run.article_id,
                slug=slug,
                topic=topic,
                format_id=format_id,
                data=output.data,
            )

            yield PipelineEvent(
                event_type="stage_complete",
                stage=stage.name,
                message=f"{stage.name} 스테이지 완료",
                data=output.data,
            )

        pipeline_run.status = PipelineStatus.COMPLETED
        pipeline_run.completed_at = datetime.now(UTC)
        total = (pipeline_run.completed_at - pipeline_run.started_at).total_seconds()
        pipeline_run.duration_seconds = round(total, 2)
        await session.commit()

        yield PipelineEvent(
            event_type="pipeline_complete",
            stage="all",
            message="파이프라인 완료",
        )
        await dispatch_webhook("pipeline_complete", {
            "run_id": pipeline_run.id,
            "article_id": pipeline_run.article_id,
            "duration_seconds": pipeline_run.duration_seconds,
        })
