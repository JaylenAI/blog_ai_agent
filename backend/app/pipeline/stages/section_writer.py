from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.claude.client import ClaudeClient
from app.claude.prompts.generator import GeneratorPrompt
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec

logger = get_logger(__name__)

MAX_SECTION_RETRIES = 2
MIN_SECTION_CHARS = 100


@dataclass(frozen=True)
class SectionResult:
    section_number: int
    heading: str
    content: str
    success: bool
    error: str = ""
    char_count: int = 0
    retry_count: int = 0


class SectionWriter:
    def __init__(self, claude: ClaudeClient, prompt: GeneratorPrompt) -> None:
        self._claude = claude
        self._prompt = prompt

    async def write_section(
        self,
        *,
        topic: str,
        title: str,
        section: dict,
        section_number: int,
        total_sections: int,
        previous_sections: list[str],
        references: str,
        seo_keywords: str,
        format_spec: FormatSpec | None,
        full_outline: str,
    ) -> SectionResult:
        heading = section.get("heading", f"섹션 {section_number}")
        key_points = "\n".join(
            f"  - {p}" for p in section.get("key_points", [])
        )

        prev_text = ""
        if previous_sections:
            recent = previous_sections[-3:]
            prev_text = "\n\n---\n\n".join(recent)

        prompt_text = self._prompt.render_section(
            topic=topic,
            title=title,
            section_heading=heading,
            section_key_points=key_points or "없음",
            section_number=str(section_number),
            total_sections=str(total_sections),
            previous_sections_text=prev_text,
            references=references,
            seo_keywords=seo_keywords,
            format_spec=format_spec,
            full_outline=full_outline,
        )

        last_error = ""
        for attempt in range(MAX_SECTION_RETRIES + 1):
            try:
                response = await self._claude.run(prompt_text)
            except (RuntimeError, TimeoutError) as e:
                logger.error(
                    "섹션 %d '%s' Claude CLI 실패: %s",
                    section_number, heading, e,
                )
                return SectionResult(
                    section_number=section_number,
                    heading=heading,
                    content="",
                    success=False,
                    error=f"섹션 '{heading}' 작성 실패: {e}",
                    retry_count=attempt,
                )

            content = response.text.strip()

            if len(content) < MIN_SECTION_CHARS:
                last_error = (
                    f"섹션 내용이 너무 짧습니다 ({len(content)}자)"
                )
                logger.warning(
                    "섹션 %d '%s' 너무 짧음 (시도 %d/%d): %d자",
                    section_number,
                    heading,
                    attempt + 1,
                    MAX_SECTION_RETRIES + 1,
                    len(content),
                )
                continue

            logger.info(
                "섹션 %d/%d '%s' 작성 완료: %d자",
                section_number,
                total_sections,
                heading,
                len(content),
            )
            return SectionResult(
                section_number=section_number,
                heading=heading,
                content=content,
                success=True,
                char_count=len(content),
                retry_count=attempt,
            )

        return SectionResult(
            section_number=section_number,
            heading=heading,
            content="",
            success=False,
            error=f"섹션 '{heading}' 작성 실패 ({MAX_SECTION_RETRIES + 1}회 시도): {last_error}",
            retry_count=MAX_SECTION_RETRIES + 1,
        )
