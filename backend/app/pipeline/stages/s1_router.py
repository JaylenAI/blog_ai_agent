from app.claude.client import ClaudeClient
from app.claude.prompts.router import RouterPrompt
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = ["slug", "title", "category", "search_queries", "seo_keywords"]


class RouterStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = RouterPrompt()

    @property
    def name(self) -> str:
        return "router"

    async def execute(self, stage_input: StageInput) -> StageOutput:
        prompt_text = self._prompt.render(topic=stage_input.topic)

        try:
            result = await self._claude.run_json(prompt_text)
        except (RuntimeError, ValueError) as e:
            logger.error("Router Claude 응답 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Claude CLI 응답 파싱 실패: {e}",
            )

        missing = [f for f in REQUIRED_FIELDS if f not in result]
        if missing:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Router 응답에 필수 필드 누락: {missing}",
            )

        meta = {
            "slug": result["slug"],
            "title": result["title"],
            "topic": stage_input.topic,
            "category": result["category"],
            "target_audience": result.get("target_audience", "intermediate"),
            "search_queries": result["search_queries"],
            "seo_keywords": result["seo_keywords"],
            "estimated_sections": result.get("estimated_sections", 7),
        }
        self._fm.write_json(stage_input.slug, "meta.json", meta)

        logger.info("Router 완료: slug=%s, title=%s", result["slug"], result["title"])

        return StageOutput(stage_name=self.name, success=True, data=result)
