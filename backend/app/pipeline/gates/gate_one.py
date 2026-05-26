from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GateOneStage(Stage):
    def __init__(self, *, auto_approve: bool = False) -> None:
        self._auto_approve = auto_approve

    @property
    def name(self) -> str:
        return "gate_one"

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: "ProgressCallback | None" = None,
    ) -> StageOutput:
        if self._auto_approve:
            logger.info("Gate 1 자동 승인 (auto_gate_one=True)")
            return StageOutput(
                stage_name=self.name,
                success=True,
                data=stage_input.data,
            )

        logger.info("Gate 1 사용자 검수 대기")
        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                **stage_input.data,
                "gate_pending": True,
            },
        )
