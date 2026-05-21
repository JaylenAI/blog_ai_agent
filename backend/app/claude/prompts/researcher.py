from app.claude.prompts.base import PromptTemplate

_OUTPUT_FORMAT = """[OUTPUT FORMAT]
{{
  "references": [
    {{
      "url": "출처 URL",
      "title": "자료 제목",
      "summary": "핵심 내용 2-3문장 요약",
      "relevance_score": 0.0~1.0
    }}
  ]
}}"""

_FOOTER = "반드시 위 형식의 JSON만 응답하세요. 다른 텍스트는 포함하지 마세요."


class OfficialLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(Official Librarian)입니다.
공식 문서, 논문, 표준 기관 자료를 중심으로 참고자료를 수집합니다.

[GOAL]
주제에 대한 공식 문서 및 권위 있는 자료를 웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERIES]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

공식 문서, 학술 논문, 표준 기관 자료를 3-5개 찾아주세요.
{_FOOTER}"""


class GithubLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(GitHub Librarian)입니다.
관련 오픈소스 프로젝트, GitHub 리포지토리, 코드 예시를 수집합니다.

[GOAL]
주제와 관련된 GitHub 리포지토리와 오픈소스 프로젝트를 웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERIES]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

관련 GitHub 리포지토리, 오픈소스 프로젝트를 3-5개 찾아주세요.
스타 수가 많고 활발히 유지되는 프로젝트를 우선하세요.
{_FOOTER}"""


class BlogEnLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(English Blog Librarian)입니다.
영문 기술 블로그 포스트, 튜토리얼, 기술 문서를 수집합니다.

[GOAL]
주제에 대한 양질의 영문 기술 블로그 글을 웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERIES]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

영문 기술 블로그, 튜토리얼을 3-5개 찾아주세요.
최근 1-2년 내 작성된 실용적인 글을 우선하세요.
{_FOOTER}"""


class BlogKrLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(Korean Blog Librarian)입니다.
한국어 기술 블로그, 네이버 D2, 카카오 기술블로그 등의 자료를 수집합니다.

[GOAL]
주제에 대한 양질의 한국어 기술 블로그 글을 웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERIES]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

한국어 기술 블로그를 3-5개 찾아주세요.
네이버 D2, 카카오 기술블로그, 우아한형제들 등 기업 기술 블로그를 우선하세요.
{_FOOTER}"""
