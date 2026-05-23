from app.images.mermaid_renderer import render_all_diagrams
from app.pipeline.base import Stage, StageInput, StageOutput
from app.publishers.html_converter import convert_for_tistory
from app.services.obsidian_service import ObsidianService
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PublisherStage(Stage):
    def __init__(
        self,
        file_manager: FileManager,
        *,
        obsidian_vault_path: str = "",
    ) -> None:
        self._fm = file_manager
        self._obsidian = ObsidianService(file_manager, obsidian_vault_path)

    @property
    def name(self) -> str:
        return "publisher"

    async def execute(self, stage_input: StageInput) -> StageOutput:
        content = self._fm.read_text(stage_input.slug, "final.md")
        if not content:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="final.md를 찾을 수 없습니다",
            )

        meta = self._fm.read_json(stage_input.slug, "meta.json") or {}

        slug_dir = self._fm.article_dir(stage_input.slug)

        rendered_count = 0
        try:
            diagram_results = await render_all_diagrams(slug_dir)
            rendered_count = sum(1 for d in diagram_results if d["success"])
        except Exception as e:
            logger.error("다이어그램 렌더링 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"다이어그램 렌더링 실패: {e}",
            )

        try:
            html_content = convert_for_tistory(content, meta)
            self._fm.write_text(stage_input.slug, "tistory.html", html_content)
        except Exception as e:
            logger.error("Tistory HTML 변환 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Tistory HTML 변환 실패: {e}",
            )

        obsidian_saved = False
        try:
            result = self._obsidian.save_article(stage_input.slug)
            obsidian_saved = result.get("success", False)
        except Exception as e:
            logger.error("Obsidian 저장 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Obsidian 저장 실패: {e}",
            )

        logger.info(
            "Publisher 완료: obsidian=%s, diagrams=%d, html=생성됨",
            obsidian_saved,
            rendered_count,
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                "obsidian_saved": obsidian_saved,
                "tistory_ready": True,
                "html_path": f"{stage_input.slug}/tistory.html",
                "content_path": f"{stage_input.slug}/final.md",
                "diagrams_rendered": rendered_count,
            },
        )
