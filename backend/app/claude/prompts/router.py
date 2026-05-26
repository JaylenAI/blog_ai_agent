from __future__ import annotations

from typing import TYPE_CHECKING

from app.claude.prompts.base import PromptTemplate

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec

ROUTER_SYSTEM = (
    "당신은 기술 블로그 자동화 시스템의 Router 에이전트입니다.\n"
    "주어진 주제를 분석하여 블로그 글 작성에 필요한 메타데이터를 JSON으로 생성합니다."
)


class RouterPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        topic = kwargs["topic"]
        format_spec: FormatSpec | None = kwargs.get("format_spec")
        all_formats: list[FormatSpec] | None = kwargs.get("all_formats")

        format_section = ""
        if format_spec:
            format_section = f"""
[ASSIGNED FORMAT]
이 글은 "{format_spec.name}" ({format_spec.id}) 형식으로 작성됩니다.
recommended_format 필드에 "{format_spec.id}"를 그대로 반환하세요.
"""
        elif all_formats:
            lines = []
            for f in all_formats:
                signals = ", ".join(f.router_signals[:5])
                lines.append(f'- {f.id} ({f.name}): {f.description} [시그널: {signals}]')
            format_list = "\n".join(lines)
            format_section = f"""
[FORMAT SELECTION]
아래 형식 목록을 참고하여 주제에 가장 적합한 형식을 recommended_format에 지정하세요.

{format_list}
"""

        return f"""[CONTEXT]
{ROUTER_SYSTEM}

{format_section}

[GOAL]
주제를 분석하고 다음 정보를 JSON으로 반환하세요.

[OUTPUT FORMAT]
{{
  "slug": "영문-소문자-하이픈-구분 (URL-safe)",
  "title": "SEO 최적화된 한국어 제목 (60자 이내)",
  "category": "카테고리 (예: AI/ML, Backend, Frontend, DevOps)",
  "target_audience": "대상 독자 수준 (beginner | intermediate | advanced)",
  "search_queries": ["주제 전체를 반영하는 구체적 검색 쿼리 6-8개 — 도구명만이 아니라 주제의 핵심 행위/목적을 포함. 한국어 2-3개 + 영어 4-5개 혼합"],
  "seo_keywords": ["SEO 키워드 정확히 10개 — 주제 핵심어 + 관련 롱테일 혼합"],
  "estimated_sections": 7,
  "recommended_format": "형식 ID (concept, tutorial, comparison, ...)"
}}

[REQUEST]
주제: {topic}

반드시 위 형식의 JSON만 응답하세요. 다른 텍스트는 포함하지 마세요."""
