from __future__ import annotations

from app.claude.client import ClaudeClient
from app.claude.prompts.generator import GeneratorPrompt
from app.config import settings
from app.formats import get_format_registry
from app.images.image_generator import ImageGenerator
from app.images.playwright_renderer import render_thumbnail
from app.pipeline.base import PipelineEvent, ProgressCallback, Stage, StageInput, StageOutput
from app.pipeline.stages.section_writer import SectionWriter
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger
from app.utils.markdown import strip_wrapping_code_fence

logger = get_logger(__name__)


class GeneratorStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = GeneratorPrompt()
        self._writer = SectionWriter(claude, self._prompt)
        self._image_gen = (
            ImageGenerator(claude, file_manager)
            if settings.image_generation_enabled
            else None
        )

    @property
    def name(self) -> str:
        return "generator"

    async def execute(
        self,
        stage_input: StageInput,
        on_progress: ProgressCallback | None = None,
    ) -> StageOutput:
        meta = self._fm.read_json(stage_input.slug, "meta.json") or {}
        outline_data = self._fm.read_json(stage_input.slug, "outline.json") or {}
        refs_data = self._fm.read_json(stage_input.slug, "references.json") or []

        outline = outline_data.get("outline", [])
        if not outline:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="아웃라인이 없습니다 (outline.json 확인 필요)",
            )

        outline_text = "\n".join(
            f"## {s.get('heading', '')}\n"
            + "\n".join(f"  - {p}" for p in s.get("key_points", []))
            for s in outline
        )

        refs_text = "\n".join(
            f"- [{r.get('title', 'N/A')}]({r.get('url', '')}): {r.get('summary', '')}"
            for r in refs_data
        )

        seo_keywords = ", ".join(meta.get("seo_keywords", []))
        format_id = meta.get("format_id", stage_input.format_id)
        registry = get_format_registry()
        format_spec = registry.get(format_id)
        total = len(outline)

        self._emit(on_progress, f"본문 작성 시작 (총 {total}개 섹션)", {
            "total_sections": total, "completed_sections": 0,
        })

        sections: list[str] = []
        for i, section in enumerate(outline):
            heading = section.get("heading", f"섹션 {i + 1}")
            self._emit(on_progress, f"섹션 {i + 1}/{total} 작성 중: {heading}", {
                "total_sections": total,
                "completed_sections": i,
                "current_section": i + 1,
                "section_heading": heading,
                "status": "writing",
            })

            result = await self._writer.write_section(
                topic=stage_input.topic,
                title=meta.get("title", stage_input.topic),
                section=section,
                section_number=i + 1,
                total_sections=total,
                previous_sections=sections[-3:],
                references=refs_text or "참고자료 없음",
                seo_keywords=seo_keywords or "키워드 없음",
                format_spec=format_spec,
                full_outline=outline_text,
            )

            if not result.success:
                return StageOutput(
                    stage_name=self.name,
                    success=False,
                    error=f"섹션 {i + 1} 작성 실패: {result.error}",
                )

            sections.append(result.content)

            self._emit(on_progress, f"섹션 {i + 1}/{total} 완료: {result.heading}", {
                "total_sections": total,
                "completed_sections": i + 1,
                "section_heading": result.heading,
                "section_char_count": result.char_count,
            })

        content = strip_wrapping_code_fence("\n\n".join(sections)).strip()
        self._fm.write_text(stage_input.slug, "final.md", content)

        char_count = len(content)
        section_count = content.count("## ")

        diagrams = _extract_mermaid_blocks(content)
        for i, diagram in enumerate(diagrams):
            self._fm.write_text(
                stage_input.slug, f"diagrams/diagram_{i + 1}.mmd", diagram
            )

        image_results: list[dict] = []
        if self._image_gen:
            self._emit(on_progress, "이미지 생성 중...", {
                "total_sections": total, "completed_sections": total,
            })
            try:
                image_results = await self._image_gen.generate_all(
                    stage_input.slug, content, stage_input.topic
                )
                successful = [r for r in image_results if r.get("success")]
                if successful:
                    content = _insert_image_references(content, successful)
                    self._fm.write_text(stage_input.slug, "final.md", content)
            except Exception as e:
                logger.warning("이미지 생성 실패 (본문은 유지): %s", e)

        image_count = sum(1 for r in image_results if r.get("success"))

        thumbnail_path = ""
        try:
            thumb_output = self._fm.images_dir(stage_input.slug) / "thumbnail.png"
            title = meta.get("title", stage_input.topic)
            category = meta.get("category", "Tech Blog")
            subtitle = stage_input.topic if title != stage_input.topic else ""
            ok = await render_thumbnail(
                thumb_output,
                title=title,
                category=category,
                subtitle=subtitle,
            )
            if ok:
                thumbnail_path = f"{stage_input.slug}/images/thumbnail.png"
        except Exception as e:
            logger.warning("썸네일 생성 실패 (본문은 유지): %s", e)

        logger.info(
            "Generator 완료: %d자, %d개 섹션, %d개 다이어그램, %d개 이미지",
            char_count, section_count, len(diagrams), image_count,
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                "content_path": f"{stage_input.slug}/final.md",
                "word_count": char_count,
                "section_count": section_count,
                "diagram_count": len(diagrams),
                "image_count": image_count,
                "thumbnail_path": thumbnail_path,
            },
        )

    def _emit(
        self,
        on_progress: ProgressCallback | None,
        message: str,
        data: dict,
    ) -> None:
        if on_progress:
            on_progress(PipelineEvent(
                event_type="stage_progress",
                stage=self.name,
                message=message,
                data=data,
            ))


def _extract_mermaid_blocks(content: str) -> list[str]:
    blocks: list[str] = []
    in_block = False
    current: list[str] = []

    for line in content.split("\n"):
        if line.strip().startswith("```mermaid"):
            in_block = True
            current = []
        elif in_block and line.strip() == "```":
            in_block = False
            blocks.append("\n".join(current))
        elif in_block:
            current.append(line)

    return blocks


def _insert_image_references(content: str, image_results: list[dict]) -> str:
    used_positions: set[int] = set()

    for img in image_results:
        alt = img.get("alt", img["filename"])
        ref = f"\n![{alt}](images/{img['filename']})\n"

        heading = img.get("insert_after_heading", "")
        inserted = False

        if heading:
            search_start = 0
            while True:
                idx = content.find(heading, search_start)
                if idx == -1:
                    break
                if idx in used_positions:
                    search_start = idx + len(heading)
                    continue
                used_positions.add(idx)
                end_of_heading = idx + len(heading)
                next_newline = content.find("\n", end_of_heading)
                if next_newline != -1:
                    para_end = content.find("\n\n", next_newline + 1)
                    insert_pos = para_end if para_end != -1 else next_newline
                    content = content[:insert_pos] + "\n" + ref + content[insert_pos:]
                else:
                    content = content + ref
                inserted = True
                break

        if not inserted:
            last_heading = content.rfind("\n## ")
            if last_heading != -1:
                para_end = content.find("\n\n", last_heading)
                if para_end != -1:
                    content = content[:para_end] + "\n" + ref + content[para_end:]
                else:
                    content = content + ref
            else:
                content = content + ref

    return content
