from app.claude.client import ClaudeClient
from app.claude.prompts.outliner import OutlinerPrompt
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = ["outline", "total_sections", "estimated_total_words"]


class OutlinerStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = OutlinerPrompt()

    @property
    def name(self) -> str:
        return "outliner"

    async def execute(self, stage_input: StageInput) -> StageOutput:
        meta = self._fm.read_json(stage_input.slug, "meta.json") or {}
        refs_data = self._fm.read_json(stage_input.slug, "references.json") or []

        refs_text = "\n".join(
            f"- [{r.get('title', 'N/A')}]({r.get('url', '')}): {r.get('summary', '')}"
            for r in refs_data
        )

        try:
            result = await self._claude.run_json(
                self._prompt.render(
                    topic=stage_input.topic,
                    title=meta.get("title", stage_input.topic),
                    category=meta.get("category", ""),
                    target_audience=meta.get("target_audience", "intermediate"),
                    references=refs_text or "참고자료 없음",
                )
            )
        except (RuntimeError, ValueError) as e:
            logger.error("Outliner Claude 응답 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Outliner 응답 처리 실패: {e}",
            )

        missing = [f for f in REQUIRED_FIELDS if f not in result]
        if missing:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Outliner 응답에 필수 필드 누락: {missing}",
            )

        self._fm.write_json(stage_input.slug, "outline.json", result)

        logger.info(
            "Outliner 완료: %d개 섹션, 예상 %d자",
            result["total_sections"],
            result["estimated_total_words"],
        )

        return StageOutput(stage_name=self.name, success=True, data=result)
