from __future__ import annotations

from app.claude.prompts.base import PromptTemplate

ORACLE_CRITERIA = [
    ("style", "비유 적절성", "각 섹션의 비유가 주제에 맞고 신선한가"),
    ("style", "흐름과 가독성", "섹션 간 전환이 자연스럽고 논리적 흐름이 있는가"),
    ("aeo", "정의 품질", "AI 답변 엔진이 인용할 만큼 명확하고 구체적인 정의가 있는가"),
    ("geo", "독창성", "단순 번역/요약이 아닌 고유한 관점이나 분석이 있는가"),
    ("style", "AI 투 감지", "기계적으로 생성된 느낌의 표현이 전반적으로 없는가"),
]


class OraclePrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        criteria_text = "\n".join(
            f"  {i+1}. [{cat}] {name}: {desc}"
            for i, (cat, name, desc) in enumerate(ORACLE_CRITERIA)
        )

        return f"""[CONTEXT]
당신은 한국어 기술 블로그의 '오라클' 검증자입니다.
자동 검증과 기본 Claude 검증을 통과한 글에 대해 더 깊은 의미 검증을 수행합니다.

[GOAL]
아래 블로그 글을 읽고 5가지 기준으로 평가하세요.

[CRITERIA]
{criteria_text}

[OUTPUT FORMAT]
{{
  "validations": [
    {{
      "category": "style|aeo|geo",
      "item": "기준명",
      "passed": true|false,
      "score": 0.0~1.0,
      "message": "구체적 평가 근거 한 줄"
    }}
  ]
}}

[SEO KEYWORDS]
{kwargs.get("seo_keywords", "없음")}

[BLOG CONTENT]
{kwargs["content"]}

[REQUEST]
각 기준에 대해 엄격하게 평가하세요.
score 0.7 미만이면 passed=false로 판정합니다.
반드시 위 형식의 JSON만 응답하세요."""
