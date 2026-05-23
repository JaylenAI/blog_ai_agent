---
tags:
  - project/blog-ai-agent
  - phase/7
date: 2026-05-21
created: 2026-05-21
updated: 2026-05-23
aliases:
  - Project Setup
  - Phase 7
  - 프로젝트 셋업
status: active
related:
  - "[[05-architecture/README]]"
  - "[[05-architecture/tech-stack]]"
  - "[[06-ux-design]]"
  - "[[08-milestones]]"
  - "[[09-development-guide]]"
---

# Phase 7 — 프로젝트 셋업

> 부록 E Phase 7. 개발 환경, 디렉토리 구조, 의존성, CI/CD, 보안 베이스라인을 정의한다.

---

## 1. 사전 요구사항

| 도구 | 최소 버전 | 용도 | 설치 확인 |
|------|----------|------|----------|
| **Python** | 3.12+ | FastAPI 백엔드 런타임 | `python3 --version` |
| **UV** | 0.7+ | Python 패키지 관리 (pip/venv/poetry 금지) | `uv --version` |
| **Node.js** | 22+ | React 프론트엔드 + mermaid-cli | `node --version` |
| **pnpm** | 10+ | Node 패키지 관리 | `pnpm --version` |
| **Git** | 2.40+ | 버전 관리 | `git --version` |
| **Claude Code** | 최신 | 하네스 런타임 (Claude Max 구독) | `claude --version` |

### 선택 도구 (Phase에 따라)

| 도구 | 시점 | 용도 |
|------|------|------|
| **Playwright** | ✅ 설치됨 | E2E 테스트 + Tistory 반자동 발행 |
| **Pillow** | ✅ 설치됨 | 이미지 후처리 (리사이즈, 메타데이터) |
| **mermaid-cli** | ✅ 설치됨 | 다이어그램 PNG 렌더링 |

---

## 2. 초기 셋업 절차

### 2-1. 저장소 초기화

```bash
cd ~/Desktop/blog/blog_ai_agent

# Git 브랜치 확인
git status
git branch -a

# dev 브랜치에서 시작 (main에 직접 작업 금지)
git checkout dev
git pull origin dev
```

### 2-2. Python 환경 (UV)

```bash
# 프로젝트 초기화 (이미 되어있으면 skip)
uv init

# 가상환경 생성
uv venv

# 런타임 의존성
uv add markdown          # md → HTML 변환
uv add pyyaml            # YAML frontmatter 파싱
uv add jsonschema        # JSON 스키마 검증 (plan, outline, critique)

# 개발 의존성
uv add --dev pytest      # 단위 테스트
uv add --dev ruff        # 린터 + 포매터
uv add --dev pytest-cov  # 커버리지

# Phase 9에서 추가할 의존성 (지금은 설치하지 않음)
# uv add playwright       # Tistory 발행
# uv add pillow           # 이미지 후처리
# uv add matplotlib       # 차트 (Could)

# 환경 동기화
uv sync
```

### 2-3. Node.js 환경 (mermaid-cli)

```bash
# mermaid-cli 로컬 설치
pnpm init
pnpm add -D @mermaid-js/mermaid-cli

# 설치 확인
pnpm exec mmdc --version
```

### 2-4. pyproject.toml 기본 설정

```toml
[project]
name = "blog-ai-agent"
version = "0.1.0"
description = "한국어 기술 블로그 E2E 자동화 AI Agent"
requires-python = ">=3.12"
license = "MIT"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "RUF"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=src --cov-report=term-missing"
```

---

## 3. 디렉토리 구조

```
blog_ai_agent/
├── CLAUDE.md                          # Claude Code 작업 규칙
├── AGENTS.md                          # Subagent/MCP 운영 가이드
├── pyproject.toml                     # Python 프로젝트 설정
├── uv.lock                           # 의존성 락 파일
├── package.json                       # Node (mermaid-cli)
├── pnpm-lock.yaml                     # Node 락 파일
├── .gitignore
├── .env.example                       # 환경변수 템플릿 (실제 .env는 gitignore)
│
├── .claude/
│   └── skills/
│       └── blog-writer/
│           └── SKILL.md               # 블로그 작성 Skill 정의
│
├── backend/                           # FastAPI 백엔드
│   ├── pyproject.toml                 # uv 기반 Python 프로젝트 설정
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 진입점 + CORS + 라이프사이클
│   │   ├── api/                       # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py            # POST /pipeline/start, GET /stream (SSE)
│   │   │   └── articles.py            # 글 목록/상세 조회
│   │   ├── pipeline/                  # 6 Stage 파이프라인
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py        # 상태 머신 총괄
│   │   │   ├── router.py              # Stage 1: 주제 분석
│   │   │   ├── researcher.py          # Stage 2: 자료수집 (4 Librarian)
│   │   │   ├── outliner.py            # Stage 3: 아웃라인 생성
│   │   │   ├── generator.py           # Stage 4: 본문 + 이미지 생성
│   │   │   ├── validator.py           # Stage 5: 30항목 검증
│   │   │   └── publisher.py           # Stage 6: Tistory 배포
│   │   ├── services/                  # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── claude_cli.py          # Claude Code CLI subprocess 래퍼
│   │   │   ├── state_store.py         # SQLite + 파일시스템 상태 관리
│   │   │   └── sse_manager.py         # SSE 이벤트 브로드캐스트
│   │   ├── models/                    # Pydantic 모델
│   │   │   ├── article.py
│   │   │   ├── pipeline_state.py
│   │   │   └── validation.py
│   │   └── utils/                     # 공용 유틸리티
│   │       ├── file_manager.py        # .sisyphus/ 디렉토리 관리
│   │       └── text_stats.py          # 글자수, 키워드 밀도 계산
│   └── tests/                         # 백엔드 테스트
│
├── frontend/                          # React + Vite 프론트엔드
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx                    # 3-pane 워크스페이스 레이아웃
│   │   ├── components/                # UI 컴포넌트
│   │   │   ├── Sidebar/
│   │   │   ├── Topbar/
│   │   │   ├── Editor/
│   │   │   ├── Launcher/
│   │   │   ├── RightPanel/
│   │   │   └── GateModals/
│   │   ├── hooks/                     # useSSE, usePipeline 등
│   │   ├── stores/                    # Zustand 상태 관리
│   │   └── styles/                    # 디자인 토큰 + CSS
│   └── public/
│
├── tests/                             # Phase 9~ 테스트
│   ├── __init__.py
│   ├── test_format_checker.py
│   ├── test_seo_checker.py
│   ├── test_md_to_html.py
│   └── test_text_stats.py
│
├── scripts/                           # 실행 스크립트
│   └── init_blog_dir.py               # .sisyphus/ 초기 구조 생성
│
├── docs/                              # 기획/설계 문서 (옵시디언 vault)
│   ├── _index.md
│   ├── README.md
│   ├── 00-elevator-pitch.md
│   ├── 01-problem-statement.md
│   ├── 02-benchmark.md
│   ├── 03-team-and-roles.md
│   ├── 04-requirements.md
│   ├── 05-architecture/
│   │   ├── README.md
│   │   ├── pipeline-stages.md
│   │   ├── research-strategy.md
│   │   ├── content-format.md
│   │   ├── validator-design.md
│   │   ├── image-pipeline.md
│   │   ├── publishing-strategy.md
│   │   └── tech-stack.md
│   ├── 06-ux-design.md
│   ├── 07-project-setup.md            ← 이 문서
│   ├── 08-milestones.md
│   ├── style-guide/
│   │   ├── blog-style.md              # STYLE.md (546줄)
│   │   └── tone-guide.md
│   ├── adr/
│   │   ├── 001-claude-agent-sdk-vs-langgraph.md
│   │   ├── 003-mermaid-vs-paid-image-api.md
│   │   └── 005-html-css-thumbnail.md
│   └── meetings/
│       └── 2026-05-20-kickoff.md
│
└── .sisyphus/                         # 런타임 작업 공간 (gitignore)
    └── blog/
        └── <YYYY-MM-DD>_<topic-slug>/
            ├── 00_plan.json
            ├── 01_research.md
            ├── 02_outline.json
            ├── 03_sections/*.md
            ├── 04_images/*.png, *.svg
            ├── 05_diagrams/*.mmd
            ├── 06_final.md
            ├── 07_critique.json
            ├── 08_tistory.html
            └── meta.json
```

---

## 4. .gitignore

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/

# 환경변수
.env
.env.local
.env.*.local

# 런타임 작업 공간 (생성 산출물)
.sisyphus/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Playwright
playwright/.auth/
*.session.json

# 빌드 산출물
*.pyc
htmlcov/
.coverage
.pytest_cache/
.ruff_cache/
```

---

## 5. .env.example

```env
# Blog AI Agent 환경 변수 템플릿
# 실제 값은 .env에 작성 (이 파일은 커밋용 템플릿)

# Tistory 블로그 URL (자동 발행 시 사용)
TISTORY_BLOG_URL=https://jaylenhan.tistory.com

# 글 생성 기본 설정
DEFAULT_SECTION_COUNT=9
DEFAULT_MIN_REFERENCES=8
DEFAULT_TARGET_LENGTH=7500

# Mermaid CLI 경로 (pnpm 로컬이면 자동 탐색)
# MMDC_PATH=./node_modules/.bin/mmdc

# Playwright 설정 (Phase 9+)
# PLAYWRIGHT_HEADLESS=false
# TISTORY_SESSION_DIR=.playwright/.auth
```

---

## 6. Claude Code Skill 구조

### 6-1. Skill 위치

```
~/.claude/skills/blog-writer/
└── SKILL.md          # 메인 Skill 정의 (546줄 양식 규칙 포함)
```

프로젝트 내에서도 심볼릭 링크 또는 복사본 유지:

```
.claude/skills/blog-writer/
└── SKILL.md
```

### 6-2. Skill 호출 방법

```bash
# Claude Code CLI에서
claude "/blog 에이전틱 RAG에 대해 다이어그램 포함해서 깊게 정리해줘"

# 또는 대화 중
> /blog MCP 서버 직접 구축 실습 (장문, Playwright 실습 포함)
```

---

## 7. MCP 서버 설정

### 7-1. 필수 MCP (Claude Code 내장 / 별도 설정)

| MCP | 용도 | 하네스 내 사용처 |
|-----|------|----------------|
| **WebSearch** | Claude Code 내장 웹 검색 | Stage 2 Researcher (librarian 4종) |
| **WebFetch** | URL → 텍스트 추출 | Stage 2 사용자 제공 링크 처리 |
| **Context7** | 공식 문서 검색 | librarian-official |
| **grep.app** | GitHub 코드 검색 | librarian-github |

### 7-2. 설정 확인

```bash
# MCP 서버 목록 확인
claude mcp list

# 필요한 MCP가 없으면 추가
# claude mcp add context7
# claude mcp add grep-app
```

---

## 8. Git 브랜치 전략

### 8-1. 초기 브랜치 구조

```
main                          ← v1.0.0 릴리스 전까지는 비어있음
└── dev                       ← 개발 통합
    ├── docs/phase-0-5        ← 완료. 이미 dev에 머지됨
    ├── docs/phase-6-8        ← 현재 작업 (이 문서 포함)
    ├── feature/pipeline-core ← Phase 9 M3: 파이프라인 코어
    ├── feature/researcher    ← Phase 9 M4: Researcher
    └── ...
```

### 8-2. 브랜치 네이밍 규칙

| 유형 | 패턴 | 예시 |
|------|------|------|
| 문서 | `docs/<scope>` | `docs/phase-6-8` |
| 기능 | `feature/<module>` | `feature/pipeline-core` |
| 버그 | `fix/<description>` | `fix/format-checker-h3` |
| 인프라 | `chore/<scope>` | `chore/mermaid-cli-setup` |

### 8-3. 머지 전략

- `feature/*` → `dev`: **Squash merge** (커밋 히스토리 정리)
- `dev` → `main`: **일반 merge** (릴리스 포인트 보존)
- `hotfix/*` → `main` + `dev`: **일반 merge** (양쪽 동기화)

---

## 9. 코드 품질 도구

### 9-1. Ruff (린터 + 포매터)

```bash
# 린트
uv run ruff check backend/app/ tests/

# 포맷
uv run ruff format backend/app/ tests/

# 자동 수정
uv run ruff check --fix backend/app/ tests/
```

### 9-2. pytest

```bash
# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=backend/app --cov-report=term-missing

# 특정 모듈
uv run pytest tests/test_format_checker.py -v
```

### 9-3. 커밋 전 체크리스트

```bash
# 1. 린트 통과
uv run ruff check backend/app/ tests/

# 2. 테스트 통과
uv run pytest

# 3. 시크릿 스캔 (수동)
grep -rn "api[_-]key\|secret\|token\|password" backend/app/ --include="*.py" | grep -v ".example"

# 4. 커버리지 80%+
uv run pytest --cov=backend/app --cov-fail-under=80
```

---

## 10. 보안 체크리스트

- [ ] `.env`가 `.gitignore`에 포함되어 있는가
- [ ] `.env.example`에 실제 값이 없는가
- [ ] 코드에 하드코딩된 API 키/토큰이 없는가
- [ ] Playwright 세션 파일이 `.gitignore`에 포함되어 있는가
- [ ] `.sisyphus/` 작업 공간이 `.gitignore`에 포함되어 있는가
- [ ] 로그에 사용자 정보/토큰을 출력하지 않는가
- [ ] 외부 유료 API를 호출하지 않는가

---

## 11. 첫 실행 검증

셋업 완료 후 아래 항목을 순서대로 확인:

```bash
# 1. Python 환경
uv run python --version          # 3.11+
uv run python -c "import yaml; print('pyyaml OK')"
uv run python -c "import markdown; print('markdown OK')"

# 2. Mermaid CLI
pnpm exec mmdc --version         # @mermaid-js/mermaid-cli 설치 확인

# 3. 린트
uv run ruff check backend/app/   # 에러 0

# 4. 테스트
uv run pytest                    # 502 tests 통과

# 5. Claude Code Skill
claude skills list               # blog-writer 표시 확인

# 6. MCP
claude mcp list                  # WebSearch, Context7, grep.app 확인

# 7. Git
git status                       # clean working tree
git branch                       # * dev
```

---

> **다음 단계**: [[08-milestones|Phase 8 마일스톤]] → [[09-development-guide|Phase 9 개발 가이드]]
