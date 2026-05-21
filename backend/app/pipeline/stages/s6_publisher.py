from datetime import datetime
from pathlib import Path

from app.images.mermaid_renderer import render_all_diagrams
from app.pipeline.base import Stage, StageInput, StageOutput
from app.publishers.html_converter import convert_for_tistory
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
        self._vault_path = obsidian_vault_path

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
        diagram_results = await render_all_diagrams(slug_dir)
        rendered_count = sum(1 for d in diagram_results if d["success"])

        html_content = convert_for_tistory(content, meta)
        self._fm.write_text(stage_input.slug, "tistory.html", html_content)

        obsidian_saved = self._save_to_obsidian(content, meta, stage_input.slug)

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

    def _save_to_obsidian(
        self, content: str, meta: dict, slug: str
    ) -> bool:
        if not self._vault_path:
            logger.info("Obsidian vault 경로 미설정 — 저장 건너뜀")
            return False

        vault = Path(self._vault_path)
        if not vault.exists():
            logger.warning("Obsidian vault 경로가 존재하지 않습니다: %s", vault)
            return False

        title = meta.get("title", slug)
        safe_title = title.replace("/", "-").replace("\\", "-")
        target = vault / f"{safe_title}.md"

        obsidian_content = _format_obsidian_note(content, meta)
        target.write_text(obsidian_content, encoding="utf-8")

        logger.info("Obsidian 저장 완료: %s", target)
        return True


def _format_obsidian_note(content: str, meta: dict) -> str:
    category = meta.get("category", "uncategorized").lower().replace("/", "-")
    title = meta.get("title", "")
    today = datetime.now().strftime("%Y-%m-%d")

    keywords = meta.get("seo_keywords", [])
    keyword_tags = "\n".join(f"  - keyword/{kw}" for kw in keywords[:5])

    frontmatter = f"""---
tags:
  - blog/published
  - category/{category}
{keyword_tags}
date: {today}
title: "{title}"
status: published
---

"""
    return frontmatter + content
