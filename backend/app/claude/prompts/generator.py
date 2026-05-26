from __future__ import annotations

from typing import TYPE_CHECKING

from app.claude.prompts.base import PromptTemplate

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec


class GeneratorPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        format_spec: FormatSpec | None = kwargs.get("format_spec")
        format_block = self._format_block(format_spec)

        cc = format_spec.structure.char_count if format_spec else None
        char_min = cc.standard[0] if cc else 6000
        char_max = cc.standard[1] if cc else 8000

        return f"""[CONTEXT]
당신은 기술 블로그 자동화 시스템의 Generator 에이전트입니다.
아웃라인에 따라 고품질 한국어 기술 블로그 글을 작성합니다.

{format_block}

[STYLE RULES]
- 톤: 격식체 100% (~합니다, ~입니다)
- 분량: {char_min:,}~{char_max:,}자
- 표: 반드시 HTML <table> 태그 사용 (마크다운 파이프 표기 금지)
- 코드 블록: 언어 명시 (```python, ```javascript 등)
- 다이어그램: Mermaid 코드 블록으로 포함 (```mermaid)
- 소제목: ## 사용 (H2)
- 각 섹션 자연스럽게 연결 (전환 문장 포함)
- FAQ 섹션 제외
- 참고 자료 목록 섹션 제외
- SEO 키워드를 자연스럽게 본문에 분포

[TOPIC]
제목: {kwargs["title"]}
주제: {kwargs["topic"]}

[OUTLINE]
{kwargs["outline"]}

[REFERENCES]
{kwargs["references"]}

[SEO KEYWORDS]
{kwargs["seo_keywords"]}

[REQUEST]
위 아웃라인에 따라 블로그 글 전체를 마크다운으로 작성하세요.
각 섹션의 key_points를 모두 다루되, 자연스러운 흐름으로 연결하세요.
참고자료를 인용할 때는 본문에 자연스럽게 녹여주세요.

마크다운 본문만 출력하세요. JSON이나 다른 형식으로 감싸지 마세요."""

    def render_section(self, **kwargs: str) -> str:
        format_spec: FormatSpec | None = kwargs.get("format_spec")
        format_block = self._format_block(format_spec)

        cc = format_spec.structure.char_count if format_spec else None
        total_min = cc.standard[0] if cc else 6000
        total_max = cc.standard[1] if cc else 8000
        total_sections = int(kwargs.get("total_sections", 8))
        per_section_min = total_min // total_sections
        per_section_max = total_max // total_sections

        section_number = int(kwargs.get("section_number", 1))
        position = (
            "글의 도입부입니다. 독자의 관심을 끄는 문장으로 시작하세요."
            if section_number == 1
            else "글의 마무리입니다. 핵심 내용을 정리하고 독자에게 다음 단계를 제시하세요."
            if section_number == total_sections
            else "글의 중간 섹션입니다. 이전 섹션과 자연스럽게 연결하세요."
        )

        prev_text = kwargs.get("previous_sections_text") or "없음 (첫 번째 섹션)"

        return f"""[CONTEXT]
당신은 기술 블로그의 한 섹션을 작성합니다.
전체 {total_sections}개 섹션 중 {section_number}번째입니다.
{position}

{format_block}

[STYLE RULES]
- 톤: 격식체 100% (~합니다, ~입니다)
- 이 섹션 분량: {per_section_min}~{per_section_max}자
- 표: 반드시 HTML <table> 태그 사용 (마크다운 파이프 표기 금지)
- 코드 블록: 언어 명시 (```python 등)
- 다이어그램: 필요 시 Mermaid 코드 블록
- SEO 키워드를 자연스럽게 분포

[TOPIC]
제목: {kwargs["title"]}
주제: {kwargs["topic"]}

[FULL OUTLINE (참고용)]
{kwargs["full_outline"]}

[PREVIOUS SECTIONS (흐름 연결용)]
{prev_text}

[CURRENT SECTION]
## {kwargs["section_heading"]}
Key Points:
{kwargs["section_key_points"]}

[REFERENCES]
{kwargs["references"]}

[SEO KEYWORDS]
{kwargs["seo_keywords"]}

[REQUEST]
위 섹션만 작성하세요. ## 소제목으로 시작하세요.
이전 섹션 내용을 참고하여 자연스럽게 연결하세요.
참고자료를 인용할 때는 본문에 자연스럽게 녹여주세요.

마크다운 본문만 출력하세요. JSON이나 다른 형식으로 감싸지 마세요."""
