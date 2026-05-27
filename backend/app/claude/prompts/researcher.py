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


def _relevance_rule(topic: str) -> str:
    return f"""[RELEVANCE RULE — 엄격 적용]
1. 반드시 '{topic}' 주제 **전체**와 직접적으로 관련된 자료만 수집하세요.
2. 주제에 사용되는 도구/라이브러리의 단순 API 레퍼런스나 공식 홈페이지는 제외하세요.
3. 주제의 **핵심 행위/목적**(예: "게임 만들기", "서버 구축", "모델 학습")을
다루는 자료를 우선하세요.
4. relevance_score 0.7 미만은 포함하지 마세요.
5. 검색 시 제공된 쿼리 힌트를 참고하되,
주제에 더 적합한 검색어를 자체적으로 만들어 추가 검색하세요."""


class OfficialLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(Official Librarian)입니다.

[GOAL]
주제에 대한 **공식 가이드, 튜토리얼, 학술 논문, 표준 문서** 중
주제를 직접 다루는 자료를 웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERY HINTS]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

다음 유형의 자료를 5-8개 찾아주세요:
- 주제를 직접 다루는 공식 튜토리얼/가이드 (단순 API 레퍼런스 페이지 X)
- 주제와 직접 관련된 학술 논문이나 기술 보고서
- 공식 문서 중 주제의 핵심 개념을 설명하는 개요/소개 페이지
- Real Python, GeeksforGeeks 등 권위 있는 교육 사이트의 관련 글

**제외 대상**: 단순 API 레퍼런스 페이지(예: pygame.Rect, numpy.array 등),
도구의 일반 홈페이지, 설치 가이드

{_relevance_rule(kwargs["topic"])}
{_FOOTER}"""


class GithubLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(GitHub Librarian)입니다.

[GOAL]
주제와 관련된 **실제 구현 프로젝트, 예제 코드, 튜토리얼 리포지토리**를
웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERY HINTS]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

다음 유형의 GitHub 리포지토리를 5-8개 찾아주세요:
- 주제를 직접 구현한 프로젝트 (예: 실제 게임, 실제 서버, 실제 모델)
- 주제에 대한 step-by-step 튜토리얼 리포지토리
- 주제 관련 awesome 리스트
- 스타 수가 많고 코드 품질이 좋은 프로젝트 우선

**제외 대상**: 주제에서 사용하는 도구/프레임워크 자체의 공식 리포지토리
(예: pygame/pygame, python/cpython)

{_relevance_rule(kwargs["topic"])}
{_FOOTER}"""


class BlogEnLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(English Blog Librarian)입니다.

[GOAL]
주제에 대한 **실전 튜토리얼, 심화 해설, 프로젝트 가이드** 영문 블로그 글을
웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERY HINTS]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

다음 유형의 영문 블로그 글을 5-8개 찾아주세요:
- 주제를 처음부터 끝까지 구현하는 step-by-step 튜토리얼
- 주제의 핵심 개념을 깊이 있게 설명하는 해설 글
- 실전 프로젝트 경험을 공유하는 기술 블로그
- Medium, Dev.to, Towards Data Science, freeCodeCamp 등 기술 블로그 플랫폼 우선

**제외 대상**: 도구/라이브러리의 일반 소개 글, 뉴스 기사, 마케팅 콘텐츠

{_relevance_rule(kwargs["topic"])}
{_FOOTER}"""


class BlogKrLibrarianPrompt(PromptTemplate):
    def render(self, **kwargs: str) -> str:
        return f"""[CONTEXT]
당신은 기술 블로그 자료조사 에이전트(Korean Blog Librarian)입니다.

[GOAL]
주제에 대한 **한국어 튜토리얼, 프로젝트 후기, 기술 해설** 블로그 글을
웹 검색하여 JSON으로 반환하세요.

{_OUTPUT_FORMAT}

[SEARCH QUERY HINTS]
{kwargs["queries"]}

[REQUEST]
주제: {kwargs["topic"]}

다음 유형의 한국어 블로그 글을 5-8개 찾아주세요:
- 주제를 직접 구현하는 한국어 튜토리얼 (티스토리, 벨로그, 네이버 블로그)
- 네이버 D2, 카카오 기술블로그, 우아한형제들 등 기업 기술 블로그
- 주제 관련 강의 노트, 프로젝트 후기
- 최근 1-2년 내 작성된 실용적인 글 우선

**제외 대상**: 도구/라이브러리의 단순 설치 가이드, 번역 글, 뉴스 기사

{_relevance_rule(kwargs["topic"])}
{_FOOTER}"""
