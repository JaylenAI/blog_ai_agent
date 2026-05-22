import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.pipeline_run import PipelineRun, PipelineStage, PipelineStatus
from app.pipeline.base import PipelineEvent, Stage, StageInput
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    def __init__(self, stages: list[Stage]) -> None:
        self._stages = stages

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
        await session.flush()

        stage_input = StageInput(
            article_id=pipeline_run.article_id,
            slug=slug,
            topic=topic,
            format_id=format_id,
        )

        first = True
        for stage in self._stages:
            pipeline_run.current_stage = PipelineStage(stage.name)
            await session.flush()

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

            try:
                output = await asyncio.wait_for(
                    stage.execute(stage_input),
                    timeout=settings.stage_timeout,
                )
            except Exception as e:
                logger.error("Stage %s 실패: %s", stage.name, e, exc_info=True)
                pipeline_run.status = PipelineStatus.FAILED
                pipeline_run.error_message = str(e)
                await session.flush()

                yield PipelineEvent(
                    event_type="stage_error",
                    stage=stage.name,
                    message=str(e),
                )
                return

            if not output.success:
                pipeline_run.status = PipelineStatus.FAILED
                pipeline_run.error_message = output.error
                await session.flush()

                yield PipelineEvent(
                    event_type="stage_error",
                    stage=stage.name,
                    message=output.error,
                )
                return

            if output.data.get("gate_pending"):
                pipeline_run.status = PipelineStatus.PAUSED
                await session.flush()

                yield PipelineEvent(
                    event_type="gate_pending",
                    stage=stage.name,
                    message=f"{stage.name} 사용자 검수 대기",
                    data=output.data,
                )
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
        await session.flush()

        yield PipelineEvent(
            event_type="pipeline_complete",
            stage="all",
            message="파이프라인 완료",
        )
