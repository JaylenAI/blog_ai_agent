---
tags:
  - project/blog-ai-agent
  - phase/5
  - docs/architecture
  - status/active
date: 2026-05-21
created: 2026-05-21
updated: 2026-05-21
aliases:
  - 파이프라인 상세
  - 6 Stage
status: active
related:
  - "[[README]]"
  - "[[research-strategy]]"
  - "[[content-format]]"
  - "[[validator-design]]"
---

# 6 Stage 파이프라인 상세

> 이 문서는 블로그 생성 파이프라인의 각 Stage를 입력/출력/도구/프롬프트/소요시간으로 정의한다.

---

## 전체 Stage 요약

| Stage | 이름 | 실행 주체 | 병렬 여부 | 소요시간 | 출력 파일 |
|-------|------|----------|----------|---------|----------|
| 1 | Router | Orchestrator 직접 | - | 10~20초 | `00_plan.json` |
| 2 | Researcher | Subagent × 4 병렬 | ✅ | 2~3분 | `references/*.md` + `01_research.md` |
| 3 | Outliner | Orchestrator 직접 | - | 30~60초 | `02_outline.json` |
| - | **Gate 1** | **사용자** | - | **3~5분** | 승인/수정 피드백 |
| 4 | Generator | Orchestrator 직접 | 부분 (이미지) | 3~5분 | `06_final.md` + `04_images/*` |
| 5 | Validator | Python + oracle | - | 30~60초 | `07_critique.json` |
| - | **Gate 2** | **사용자** | - | **10~15분** | 승인/수정 피드백 |
| 6 | Publisher | Orchestrator 직접 | - | 1~2분 | `08_tistory.html` |

**자동 합계**: 7~12분 / **수동 합계**: 13~20분 / **총합**: 20~30분

---

## Stage 1: Router (주제 분석)

### 목적

사용자의 자연어 입력을 파이프라인이 처리할 수 있는 구조화된 계획으로 변환한다.

### 입력

```
사용자 입력: "에이전틱 RAG 블로그 만들어줘"
(선택) 참고 링크: ["https://example.com/article"]
(선택) 추가 지시: "장문으로, 코드 예시 많이"
```

### 처리

1. **주제 추출**: 핵심 주제어 + 관련 키워드 도출
2. **카테고리 결정**: `[AI/LLM]`, `[DevOps]`, `[Backend]` 등
3. **분량 결정**: 표준(7~9개) / 장문(9~11개) / 초장문(11~13개)
4. **SEO 키워드 계획**:
   - 주 키워드 2개
   - 부 키워드 (분야/기술/제품/트렌드 각 2개)
5. **검색 쿼리 생성**: Stage 2에서 사용할 검색어 5~8개

### 출력 (`00_plan.json`)

```json
{
  "topic": "에이전틱 RAG (Agentic RAG)",
  "category": "[AI/LLM]",
  "level": "standard",
  "section_count": 9,
  "target_length": "6000-8000자",
  "seo": {
    "primary_keywords": ["에이전틱 RAG", "Agentic RAG"],
    "tags": [
      "#에이전틱RAG", "#AgenticRAG",
      "#AI검색", "#LLM응용",
      "#RAG파이프라인", "#벡터검색",
      "#LangChain", "#LlamaIndex",
      "#AI에이전트2026", "#2026"
    ],
    "meta_description": "에이전틱 RAG(Agentic RAG)란 기존 RAG에 자율 판단 능력을 부여한..."
  },
  "search_queries": {
    "ko": ["에이전틱 RAG 가이드 2026", "Agentic RAG 구현 방법"],
    "en": ["Agentic RAG tutorial 2026", "Agentic RAG vs RAG comparison", "Agentic RAG architecture LangChain"]
  },
  "user_refs": ["https://example.com/article"],
  "created_at": "2026-05-21T10:00:00"
}
```

### 도구

- 없음 (Orchestrator 내부 추론만)

### 소요시간: 10~20초

---

## Stage 2: Researcher (자료수집)

### 목적

3채널(자동 웹서칭 + 유저 제공 + 크롤링)에서 8~15개 신뢰할 만한 자료를 수집하고 표준 형식으로 저장한다.

### 입력

- `00_plan.json`의 `search_queries` + `user_refs`

### 처리

**4개 librarian Subagent 병렬 실행:**

```
librarian-official (공식문서 2~3개)
  └─ 검색: "{주제} official documentation" + site:github.com/docs
  └─ 전략: Getting Started, API Reference, Architecture 우선
  └─ 도구: WebSearch → WebFetch

librarian-github (GitHub 2~3개)
  └─ 검색: "{주제} github stars:>100"
  └─ 전략: README, 아키텍처 문서, 주요 이슈
  └─ 도구: WebSearch → WebFetch + grep.app

librarian-blog-en (영문블로그 2~3개)
  └─ 검색: "{주제} tutorial guide 2025 OR 2026"
  └─ 전략: dev.to, medium, 개인 블로그 심층 가이드
  └─ 도구: WebSearch → WebFetch

librarian-blog-kr (한글블로그 2~3개)
  └─ 검색: "{주제} 사용법 가이드 2025 OR 2026"
  └─ 전략: 벨로그, 티스토리, 네이버 블로그
  └─ 도구: WebSearch → WebFetch
```

**유저 제공 자료 처리 (동시):**

```
링크 → WebFetch → 표준 형식 변환 (type: user-provided, relevance: 5)
텍스트 → 직접 .md 저장 (type: user-provided, relevance: 5)
```

**수집 후 처리:**

1. 중복 URL 제거
2. 신뢰도 자동 평가 (공식문서 5 / GitHub 4 / 블로그 3 / 유저제공 5)
3. 표준 형식으로 변환 (→ [[research-strategy]] 참조)
4. `references/{slug}/`에 저장
5. 수집 요약 보고서 `01_research.md` 생성

### 출력

```
references/agentic-rag/
├── ref-001-official-langchain.md       (relevance: 5)
├── ref-002-official-llamaindex.md      (relevance: 5)
├── ref-003-github-langchain-rag.md     (relevance: 4)
├── ref-004-github-phidata-agent.md     (relevance: 4)
├── ref-005-blog-en-deeplearning.md     (relevance: 3)
├── ref-006-blog-en-medium.md           (relevance: 3)
├── ref-007-blog-kr-velog.md            (relevance: 3)
├── ref-008-blog-kr-tistory.md          (relevance: 3)
└── ref-009-user-provided.md            (relevance: 5)

.sisyphus/blog/2026-05-21_agentic-rag/
└── 01_research.md                      (수집 요약 보고서)
```

### 최소 기준

- 총 8개 이상 수집. 미달 시 사용자에게 보고
- 유저 제공 자료는 카운트에 포함
- 6개 버킷 중 최소 3개 버킷에서 수집 (Should: 4개 이상)

### 도구

- WebSearch MCP (검색)
- WebFetch MCP (내용 추출)
- Context7 MCP (공식 라이브러리 문서, 선택)
- grep.app MCP (GitHub 코드 사례, 선택)
- Playwright MCP (동적 페이지, 선택)

### 소요시간: 2~3분 (병렬)

---

## Stage 3: Outliner (아웃라인 생성)

### 목적

수집된 자료와 STYLE.md 규칙을 기반으로 7~9개 대섹션 아웃라인을 생성한다.

### 입력

- `00_plan.json` (주제, 키워드, 분량)
- `01_research.md` (수집 요약)
- `references/{slug}/*.md` (수집 자료 전체)
- STYLE.md (양식 규칙)

### 처리

1. STYLE.md 권장 구조 적용:
   ```
   1. 들어가며
   2. [개념]이란?
   3. 핵심 구성요소
   4. 특징 및 장단점
   5. 주요 활용 분야
   6. [실습] 설치·구축
   7. 한 눈에 비교
   8. 마치며
   ```
2. 각 섹션에 참고자료 매핑 (어떤 자료를 어디에 활용할지)
3. 각 섹션에 예정 요소 명시 (표/코드/콜아웃/비유)
4. SEO 키워드 H2/H3 배치 계획
5. AEO 정의문 배치 계획
6. 이미지 배치 계획 (어떤 다이어그램을 어디에)

### 출력 (`02_outline.json`)

```json
{
  "title": "[AI/LLM] 에이전틱 RAG(Agentic RAG) 완벽 가이드 2026",
  "sections": [
    {
      "id": "s1",
      "h2": "## 1. 들어가며",
      "purpose": "배경 + 왜 읽어야 하는지",
      "key_point": "기존 RAG의 한계 → 에이전틱 RAG의 등장 배경",
      "refs": ["ref-001", "ref-005"],
      "elements": {
        "table": 0,
        "code": 0,
        "callout": 1,
        "metaphor": "도서관 사서 비유"
      },
      "aeo_definition": "에이전틱 RAG란 기존 RAG 파이프라인에 자율 판단 능력을 부여한 차세대 검색 증강 생성 기법이다.",
      "image": null
    },
    {
      "id": "s2",
      "h2": "## 2. 에이전틱 RAG(Agentic RAG)란?",
      "h3s": [
        "### 2-1. 정의",
        "### 2-2. 등장 배경",
        "### 2-3. 기존 RAG와의 차이"
      ],
      "refs": ["ref-001", "ref-002", "ref-006"],
      "elements": {
        "table": 1,
        "code": 2,
        "callout": 1,
        "metaphor": "수동 vs 자율 검색 비유"
      },
      "image": "01-agentic-rag-architecture.mmd"
    }
  ],
  "images_plan": [
    {"file": "01-agentic-rag-architecture.mmd", "type": "mermaid", "location": "s2"},
    {"file": "02-agentic-rag-lifecycle.mmd", "type": "mermaid", "location": "s3"},
    {"file": "03-comparison-chart.svg", "type": "svg", "location": "s7"}
  ],
  "total_sections": 9,
  "estimated_length": "7500자"
}
```

### 도구

- 없음 (Orchestrator 내부 추론)

### 소요시간: 30~60초

### 🛑 Gate 1: 아웃라인 승인

아웃라인 생성 후 반드시 사용자에게 제시:

```
아웃라인 검수 요청:
① 제목: [AI/LLM] 에이전틱 RAG(Agentic RAG) 완벽 가이드 2026
② 대섹션 9개:
   1. 들어가며
   2. 에이전틱 RAG란?
   ...
③ 이미지 3장: 아키텍처(Mermaid) + 라이프사이클(Mermaid) + 비교(SVG)
④ 참고자료 10개 확보 완료
⑤ 예상 분량: 7,500자

진행할까요? (수정 사항 있으면 말씀해주세요)
```

---

## Stage 4: Generator (본문 + 이미지 생성)

### 목적

승인된 아웃라인을 기반으로 STYLE.md 100% 준수 본문을 작성하고, 이미지를 병렬 생성한다.

### 입력

- `02_outline.json` (승인된 아웃라인)
- `references/{slug}/*.md` (수집 자료)
- STYLE.md (양식 규칙)
- `00_plan.json` (SEO 키워드)

### 처리

**본문 작성 (섹션별 호출):**

`SectionWriter` 모듈이 각 섹션을 독립적인 Claude CLI 호출로 작성. `stage_progress` 이벤트를 통해 "작성 중"/"완료" 상태가 실시간 SSE 스트리밍으로 프론트엔드에 전달됨. 각 섹션마다 다음을 보장:
1. STYLE.md 톤 (격식체 `~합니다/~입니다`)
2. HTML `<table>` 태그 표 최소 1개
3. 코드 블록 2~5개 (목적 주석 포함)
4. 콜아웃 박스 1개+ (`💡`/`⚠️`/`🔥`/`📌`)
5. 비유 1개 (섹션마다 다른 비유, 재사용 금지)
6. AEO 정의문 (첫 문단)
7. 참고자료 코드 유사도 <30%

**이미지 생성 (본문과 병렬):**

1. Mermaid `.mmd` 파일 작성
2. `mmdc -i input.mmd -o output.png -t dark --width 1200` 실행
3. SVG 비교도/차트 직접 작성
4. matplotlib 데이터 차트 (필요 시)

**통합:**

1. 섹션별 `.md` 파일 → 하나의 `06_final.md`로 병합
2. 이미지 경로 삽입: `![alt](../images/{slug}/{file})`
3. JSON-LD TechArticle + HowTo schema 삽입
4. 카테고리 태그 10개 삽입

### 출력

```
.sisyphus/blog/2026-05-21_agentic-rag/
├── 03_sections/
│   ├── s1-intro.md
│   ├── s2-definition.md
│   ├── ...
│   └── s9-conclusion.md
├── 04_images/
│   ├── 01-agentic-rag-architecture.png
│   ├── 01-agentic-rag-architecture.mmd
│   ├── 02-agentic-rag-lifecycle.png
│   ├── 02-agentic-rag-lifecycle.mmd
│   └── 03-comparison-chart.svg
├── 05_diagrams/
│   └── (Mermaid 소스 백업)
└── 06_final.md (통합 본문)
```

### 도구

- mermaid-cli (`mmdc`) — 다이어그램 PNG 변환
- Python matplotlib — 데이터 차트 (선택)
- Bash — 파일 조작

### 소요시간: 3~5분

---

## Stage 5: Validator (품질 검증)

### 목적

생성된 글이 STYLE.md, SEO, AEO, GEO 규칙을 모두 만족하는지 자동 + 의미적으로 검증한다.

### 입력

- `06_final.md`
- STYLE.md (양식 규칙)
- `references/{slug}/*.md` (코드 유사도 비교용)

### 처리

**1단계: 자동 검증 (Python 스크립트)**

14항목 체크리스트 (→ [[validator-design]] 상세):

```
 1. 존댓말 일관성 (정규식: "~요" 반말체 탐지)
 2. 카테고리 태그 개수 (정확히 10개)
 3. 대섹션 수 (7~9개)
 4. 분량 (글자 수 ±15%)
 5. 중복 노출 (버전/수치/비유 출현 횟수)
 6. 코드 블록 수 (섹션당 2~5개)
 7. 콜아웃 박스 수 (3개 이상)
 8. FAQ 섹션 존재 여부 (없어야 함)
 9. 참고자료 섹션 존재 여부 (없어야 함)
10. JSON-LD schema 존재 확인
11. SEO 키워드 밀도 (1~2%)
12. 이미지 alt 태그 존재 확인
13. 마치며 섹션 존재 + 3단 서사 여부
14. 📝 정리 섹션 (불릿 5~7개)
```

**2단계: 의미적 검증 (oracle Subagent, 선택)**

자동 검증 통과 후, 심각한 위반이 있었거나 장문 글일 때만 실행:
- 비유의 적절성/신선함
- 가독성/흐름
- AEO 정의문 품질
- GEO 독창적 관점 존재 여부
- AI 슬롭 패턴 검출

**3단계: Reflection (위반 시)**

위반 항목 발견 → 해당 섹션만 재작성 → 재검증. 최대 2회 반복.

### 출력 (`07_critique.json`)

```json
{
  "auto_check": {
    "passed": 13,
    "failed": 1,
    "details": [
      {"item": "단점 섹션 나열식", "status": "FAIL", "fix": "4개 카테고리로 통합"}
    ]
  },
  "oracle_check": {
    "invoked": false,
    "reason": "자동 검증 1건만 위반, 경미"
  },
  "reflection_count": 1,
  "final_status": "PASS"
}
```

### 도구

- Python 스크립트 (`validators/format_checker.py`, `seo_checker.py`, `duplicate_checker.py`)
- oracle Subagent (선택)

### 소요시간: 30~60초

---

## Stage 6: Publisher (포스팅)

### 목적

검증 통과된 최종 글을 Tistory 호환 HTML로 변환하고, 포스팅을 지원한다.

### 입력

- `06_final.md` (검증 통과 본문)
- `04_images/*.png, *.svg` (이미지 파일)

### 처리

**1단계: 마크다운 → HTML 변환**

- 코드 블록 → `<pre><code>` 변환 (Tistory 호환)
- HTML `<table>` → 유지 (이미 HTML)
- 이미지 → 플레이스홀더 `<!-- IMAGE: {filename} -->` 삽입
- 콜아웃 박스 → Tistory 인용구 + 이모지 형태
- JSON-LD schema → `<script>` 태그로 삽입

**2단계: 이미지 처리**

현재 방식 (1단계):
- 이미지 파일을 `images/{slug}/`에 복사
- 사용자에게 "이미지를 Tistory 에디터에 업로드 후 URL을 알려주세요" 요청
- URL 받으면 플레이스홀더를 실제 URL로 치환

향후 방식 (2단계, Should Have):
- Playwright로 Tistory 에디터에 이미지 자동 업로드
- 업로드된 URL 자동 추출 → 플레이스홀더 치환

**3단계: 최종 출력**

- `08_tistory.html` 저장
- `posts/{slug}.md` 에 최종 마크다운 보관
- 클립보드에 HTML 복사 (pbcopy)

### 출력

```
.sisyphus/blog/2026-05-21_agentic-rag/
└── 08_tistory.html

posts/
└── agentic-rag-guide.md

images/
└── agentic-rag/
    ├── 01-agentic-rag-architecture.png
    ├── 02-agentic-rag-lifecycle.png
    └── 03-comparison-chart.svg
```

### 도구

- Python (`converters/md_to_tistory.py`)
- Playwright (향후, Should Have)
- Bash (`pbcopy`)

### 소요시간: 1~2분

---

## Stage 간 인터페이스 규약

| From → To | 인터페이스 | 형식 |
|-----------|----------|------|
| 1 → 2 | `00_plan.json` | JSON (검색 쿼리, 키워드) |
| 2 → 3 | `01_research.md` + `references/*.md` | Markdown (표준 형식) |
| 3 → Gate 1 | `02_outline.json` | JSON (섹션 구조) |
| Gate 1 → 4 | 승인 + 수정 피드백 | 자연어 |
| 4 → 5 | `06_final.md` + `04_images/*` | Markdown + 이미지 |
| 5 → Gate 2 | `07_critique.json` + `06_final.md` | JSON + Markdown |
| Gate 2 → 6 | 승인 + 수정 피드백 | 자연어 |
| 6 → 사용자 | `08_tistory.html` + 클립보드 | HTML |

---

## 에러 처리 정책

| 에러 상황 | 대응 | 자동/수동 |
|----------|------|----------|
| 자료수집 8개 미달 | 사용자에게 보고 + 진행/재시도 선택 | 수동 |
| WebSearch 실패 | 3회 재시도 후 해당 librarian 스킵, 나머지로 진행 | 자동 |
| mmdc 실행 실패 | 에러 로그 표시 + Mermaid 코드 직접 제시 | 반자동 |
| Critic 2회 반복 후에도 위반 | 사용자에게 위반 항목 보고 + 수동 수정 요청 | 수동 |
| 분량 목표 미달 (<±15%) | 부족한 섹션 식별 → 사용자에게 확장 여부 문의 | 수동 |

---

## 🔗 관련 문서

- [[research-strategy|자료수집 상세]] (Stage 2)
- [[content-format|콘텐츠 양식 상세]] (Stage 4)
- [[validator-design|검증 시스템 상세]] (Stage 5)
- [[publishing-strategy|포스팅 상세]] (Stage 6)
- [[image-pipeline|이미지 생성 상세]] (Stage 4 보조)
