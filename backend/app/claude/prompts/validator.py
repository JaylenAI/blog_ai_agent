from __future__ import annotations

from typing import TYPE_CHECKING

from app.claude.prompts.base import PromptTemplate

if TYPE_CHECKING:
    from app.formats.schema import FormatSpec

CLAUDE_VALIDATION_ITEMS = [
    ("style", "격식체 사용 (~합니다/~입니다)"),
    ("style", "자연스러운 섹션 간 흐름"),
    ("seo", "키워드 자연스러운 분포"),
    ("seo", "첫 단락 핵심 요약 (메타 설명용)"),
    ("seo", "H2 소제목 키워드 포함"),
    ("aeo", "질문-답변 구조 포함"),
    ("aeo", "구조화된 정의/목록/비교"),
    ("aeo", "단계별 설명 포함"),
    ("aeo", "핵심 요약 문장 존재"),
    ("geo", "인용 가능한 통계/사실 포함"),
    ("geo", "권위 있는 출처 인용"),
    ("geo", "최신 정보 반영"),
    ("geo", "독립적 섹션 구조"),
]


class ValidatorPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        format_spec: FormatSpec | None = kwargs.get("format_spec")

        items_text = "\n".join(
            f'  - category: "{cat}", item: "{item}"'
            for cat, item in CLAUDE_VALIDATION_ITEMS
        )

        format_context = ""
        if format_spec:
            format_context = f"""
[FORMAT CONTEXT]
이 글은 "{format_spec.name}" ({format_spec.id}) 형식으로 작성되었습니다.
{format_spec.prompt_instructions}

형식 적합성도 함께 평가하세요:
- 서두 스타일이 "{format_spec.structure.intro_style}" 패턴을 따르는가
- 마무리 스타일이 "{format_spec.structure.closing_style}" 패턴을 따르는가
- 필수 섹션이 모두 포함되어 있는가: {", ".join(format_spec.structure.required_sections)}
"""

        return f"""[CONTEXT]
당신은 기술 블로그 품질 검증 에이전트(Validator)입니다.
블로그 글을 읽고 각 검증 항목의 통과 여부를 평가합니다.

{format_context}

[GOAL]
아래 블로그 글을 읽고 각 검증 항목에 대해 평가 결과를 JSON으로 반환하세요.

[VALIDATION ITEMS]
{items_text}

[OUTPUT FORMAT]
{{
  "validations": [
    {{
      "category": "style",
      "item": "항목명",
      "passed": true,
      "score": 0.0~1.0,
      "message": "평가 결과 한 줄 설명"
    }}
  ]
}}

[SEO KEYWORDS]
{kwargs["seo_keywords"]}

[BLOG CONTENT]
{kwargs["content"]}

[REQUEST]
위 블로그 글을 모든 검증 항목에 대해 평가하세요.
반드시 위 형식의 JSON만 응답하세요."""
