from __future__ import annotations

from typing import TYPE_CHECKING

from app.claude.prompts.base import PromptTemplate

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec


class OutlinerPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        format_spec: FormatSpec | None = kwargs.get("format_spec")
        format_block = self._format_block(format_spec)

        sc = format_spec.structure.section_count if format_spec else None
        section_min = sc.min if sc else 7
        section_max = sc.max if sc else 9

        cc = format_spec.structure.char_count if format_spec else None
        char_min = cc.standard[0] if cc else 6000
        char_max = cc.standard[1] if cc else 8000

        return f"""[CONTEXT]
당신은 기술 블로그 자동화 시스템의 Outliner 에이전트입니다.
주어진 주제와 참고자료를 바탕으로 블로그 글의 상세 아웃라인을 생성합니다.

{format_block}

[RULES]
- 섹션 수: {section_min}~{section_max}개
- 총 분량: {char_min:,}~{char_max:,}자 목표
- 각 섹션에 다룰 핵심 포인트 3~5개
- 참고자료 URL을 관련 섹션에 매핑
- FAQ 섹션 제외
- 참고 자료 목록 섹션 제외

[GOAL]
아래 주제와 참고자료를 분석하여 블로그 글의 상세 아웃라인을 JSON으로 생성하세요.

[OUTPUT FORMAT]
{{
  "outline": [
    {{
      "section_number": 1,
      "heading": "1. 들어가며",
      "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
      "estimated_words": 500,
      "reference_urls": ["https://참고자료-url"]
    }}
  ],
  "total_sections": {section_min},
  "estimated_total_words": {char_min},
  "approach": "설명형 | 비교분석형 | 튜토리얼형 | 사례분석형"
}}

[TOPIC]
제목: {kwargs["title"]}
주제: {kwargs["topic"]}
카테고리: {kwargs["category"]}
대상 독자: {kwargs["target_audience"]}

[REFERENCES]
{kwargs["references"]}

[REQUEST]
위 주제와 참고자료를 바탕으로 블로그 글의 아웃라인을 생성하세요.
반드시 위 형식의 JSON만 응답하세요. 다른 텍스트는 포함하지 마세요."""
