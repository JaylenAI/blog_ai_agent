from app.claude.client import ClaudeClient
from app.claude.prompts.generator import GeneratorPrompt
from app.pipeline.base import Stage, StageInput, StageOutput
from app.utils.file_manager import FileManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeneratorStage(Stage):
    def __init__(self, claude: ClaudeClient, file_manager: FileManager) -> None:
        self._claude = claude
        self._fm = file_manager
        self._prompt = GeneratorPrompt()

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

        try:
            response = await self._claude.run(
                self._prompt.render(
                    topic=stage_input.topic,
                    title=meta.get("title", stage_input.topic),
                    outline=outline_text,
                    references=refs_text or "참고자료 없음",
                    seo_keywords=seo_keywords or "키워드 없음",
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

        logger.info(
            "Generator 완료: %d자, %d개 섹션, %d개 다이어그램",
            char_count,
            section_count,
            len(diagrams),
        )

        return StageOutput(
            stage_name=self.name,
            success=True,
            data={
                "content_path": f"{stage_input.slug}/final.md",
                "word_count": char_count,
                "section_count": section_count,
                "diagram_count": len(diagrams),
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
