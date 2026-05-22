from app.claude.client import ClaudeClient
from app.claude.prompts.generator import GeneratorPrompt
from app.config import settings
from app.formats import get_format_registry
from app.images.image_generator import ImageGenerator
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeneratorStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = GeneratorPrompt()
        self._image_gen = (
            ImageGenerator(claude, file_manager)
            if settings.image_generation_enabled
            else None
        )

    @property
    def name(self) -> str:
        return "generator"

    async def execute(self, stage_input: StageInput) -> StageOutput:
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

        try:
            response = await self._claude.run(
                self._prompt.render(
                    topic=stage_input.topic,
                    title=meta.get("title", stage_input.topic),
                    outline=outline_text,
                    references=refs_text or "참고자료 없음",
                    seo_keywords=seo_keywords or "키워드 없음",
                    format_spec=format_spec,
                )
            )
        except RuntimeError as e:
            logger.error("Generator Claude 응답 실패: %s", e)
            return StageOutput(
                stage_name=self.name,
                success=False,
                error=f"Generator 실행 실패: {e}",
            )

        content = response.text.strip()
        if not content:
            return StageOutput(
                stage_name=self.name,
                success=False,
                error="Generator가 빈 응답을 반환했습니다",
            )

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

        logger.info(
            "Generator 완료: %d자, %d개 섹션, %d개 다이어그램, %d개 이미지",
            char_count,
            section_count,
            len(diagrams),
            image_count,
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
            },
        )


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
    for img in image_results:
        alt = img.get("alt", img["filename"])
        ref = f"\n![{alt}](images/{img['filename']})\n"

        heading = img.get("insert_after_heading", "")
        if heading and heading in content:
            idx = content.index(heading) + len(heading)
            next_newline = content.find("\n", idx)
            if next_newline != -1:
                para_end = content.find("\n\n", next_newline + 1)
                insert_pos = para_end if para_end != -1 else next_newline
                content = content[:insert_pos] + "\n" + ref + content[insert_pos:]
            else:
                content = content + ref
        else:
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
