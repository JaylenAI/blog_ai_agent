from app.claude.prompts.base import PromptTemplate

ROUTER_SYSTEM = (
    "당신은 기술 블로그 자동화 시스템의 Router 에이전트입니다.\n"
    "주어진 주제를 분석하여 블로그 글 작성에 필요한 메타데이터를 JSON으로 생성합니다."
)

ROUTER_TEMPLATE = """[CONTEXT]
{system}

[GOAL]
주제를 분석하고 다음 정보를 JSON으로 반환하세요.

[OUTPUT FORMAT]
{{
  "slug": "영문-소문자-하이픈-구분 (URL-safe)",
  "title": "SEO 최적화된 한국어 제목 (60자 이내)",
  "category": "카테고리 (예: AI/ML, Backend, Frontend, DevOps)",
  "target_audience": "대상 독자 수준 (beginner | intermediate | advanced)",
  "search_queries": ["자료 조사용 검색 쿼리 4-6개"],
  "seo_keywords": ["SEO 키워드 5-10개"],
  "estimated_sections": 7
}}

[REQUEST]
주제: {topic}

반드시 위 형식의 JSON만 응답하세요. 다른 텍스트는 포함하지 마세요."""


class RouterPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        topic = kwargs["topic"]
        return ROUTER_TEMPLATE.format(system=ROUTER_SYSTEM, topic=topic)
