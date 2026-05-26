from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GateTwoStage(Stage):
    @property
    def name(self) -> str:
        return "gate_two"

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: "ProgressCallback | None" = None,
    ) -> StageOutput:
        logger.info("Gate 2 최종 검수 대기 (자동 통과 불가)")
        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                **stage_input.data,
                "gate_pending": True,
            },
        )
