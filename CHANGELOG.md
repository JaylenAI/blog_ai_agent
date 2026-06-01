# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

이 프로젝트의 모든 주요 변경 사항을 기록합니다.
[Keep a Changelog](https://keepachangelog.com/) 형식을 따르며,
[유의적 버전](https://semver.org/lang/ko/)을 준수합니다.

---

## EN v0.1.1 — Markdown Fence Fix + E2E Stabilization + Dependency Cleanup

> Release date: 2026-06-01

### Added
- **`strip_wrapping_code_fence` utility** — backend (`app/utils/markdown.py`) and frontend (`components/editor/strip-fence.ts`) helpers that remove an outer ` ```markdown ` fence wrapping an entire document while preserving real inner code blocks (` ```bash ` etc.). 14 new unit tests (7 backend + 7 frontend).
- **Rate-limit exempt paths** — `RateLimiterMiddleware` now skips monitoring endpoints (`/api/v1/health*`), so liveness checks never return 429. 2 new tests.
- **`E2E_PORT` / `E2E_HOST` env support** — `playwright.config.ts` reads the target port from env with `strictPort`, so tests no longer break when port 5173 is occupied by another app.
- **`dismissModalIfPresent` E2E helper** — closes a restored Gate modal whose scrim would otherwise intercept sidebar clicks.

### Fixed
- **```markdown fence pollution** — Generator (Claude) wrapped the whole article in a ` ```markdown ... ``` ` fence, causing the renderer to show the entire body as one code block. Fixed at the generation layer (`SectionWriter`, `s4_generator`), reinforced in the Generator prompt, and defended at the render layer (`MarkdownRenderer`).
- **`httpx` import crash** — `httpx` was imported at runtime (`webhook_service`) but declared only as a dev dependency, so a clean `uv sync` / CI run crashed the backend with `ModuleNotFoundError`. Moved to runtime `dependencies`.
- **Dev tools missing under `uv sync`** — `pytest`, `pytest-asyncio`, `ruff`, `mypy` lived in `[project.optional-dependencies]` (an extra), so plain `uv sync` and CI (`uv run pytest`) skipped them. Moved all dev tools to `[dependency-groups].dev`, which uv installs by default.
- **E2E false skips on 429** — `isBackendUp()` treated a `429` (rate limit) response as "backend down", silently skipping backend-dependent tests. It now accepts `429` as alive.
- **Hardcoded `localhost:5173` in specs** — `phase4-qa` / `phase7-qa` specs hit the wrong app; replaced with baseURL-relative paths.

### Changed
- Backend tests: 600 → **609 passing** (88% coverage).
- Frontend unit tests: 369 → **376 passing**; E2E **48 passing** (CI 1-worker, fully green).
- API surface documented as **49 endpoints** (added calendar 3 + webhooks 4 to the README count).
- Version bumped to **0.1.1** (`backend/pyproject.toml`, `frontend/package.json`).

---

## KR v0.1.1 — 마크다운 펜스 수정 + E2E 안정화 + 의존성 정리

> 릴리스 날짜: 2026-06-01

### 추가
- **`strip_wrapping_code_fence` 유틸** — 백엔드(`app/utils/markdown.py`)와 프론트엔드(`components/editor/strip-fence.ts`)에 글 전체를 감싼 바깥 ` ```markdown ` 펜스만 제거하고 본문 내 정상 코드블록(` ```bash ` 등)은 유지하는 헬퍼 추가. 신규 단위 테스트 14건(백엔드 7 + 프론트 7).
- **Rate limit 제외 경로** — `RateLimiterMiddleware`가 모니터링 엔드포인트(`/api/v1/health*`)를 제외해 생존 확인이 429를 반환하지 않도록 함. 신규 테스트 2건.
- **`E2E_PORT` / `E2E_HOST` 환경변수 지원** — `playwright.config.ts`가 대상 포트를 환경변수로 받고 strictPort 적용. 5173을 다른 앱이 점유해도 테스트가 깨지지 않음.
- **`dismissModalIfPresent` E2E 헬퍼** — 복원된 Gate 모달의 scrim이 사이드바 클릭을 가로채는 문제를 방지.

### 수정
- **```markdown 펜스 오염** — Generator(Claude)가 글 전체를 ` ```markdown ... ``` ` 펜스로 감싸 반환해 렌더러가 본문 전체를 하나의 코드블록으로 표시하던 문제. 생성 단계(`SectionWriter`, `s4_generator`)에서 제거하고, Generator 프롬프트로 예방하며, 렌더링 단계(`MarkdownRenderer`)에서 한 번 더 방어.
- **`httpx` import 크래시** — `httpx`가 런타임(`webhook_service`)에서 import되는데 dev 의존성으로만 선언돼, 깨끗한 `uv sync`/CI에서 `ModuleNotFoundError`로 백엔드가 죽던 문제. 런타임 `dependencies`로 이동.
- **`uv sync` 시 dev 도구 누락** — `pytest`, `pytest-asyncio`, `ruff`, `mypy`가 `[project.optional-dependencies]`(extra)에 있어 일반 `uv sync`와 CI(`uv run pytest`)에서 설치되지 않던 문제. uv가 기본 설치하는 `[dependency-groups].dev`로 이전.
- **429에 의한 E2E 오탐 skip** — `isBackendUp()`이 `429`(rate limit)를 "백엔드 다운"으로 오판해 백엔드 의존 테스트를 조용히 skip하던 문제. `429`도 "살아있음"으로 처리.
- **spec 내 `localhost:5173` 하드코딩** — `phase4-qa` / `phase7-qa`가 엉뚱한 앱을 호출하던 문제. baseURL 상대경로로 교체.

### 변경
- 백엔드 테스트: 600 → **609건 통과** (커버리지 88%).
- 프론트엔드 유닛 테스트: 369 → **376건 통과**, E2E **48건 통과** (CI 1-worker, 전부 green).
- API 표면을 **49개 엔드포인트**로 문서화 (README에 calendar 3 + webhooks 4 반영).
- 버전 **0.1.1**로 상향 (`backend/pyproject.toml`, `frontend/package.json`).

---

## EN v0.1.0 — Initial MVP Release: 6-Stage Pipeline + Web Platform

> Release date: 2026-05-26

### Added
- **6-Stage automation pipeline** — Router → Researcher → Outliner → Generator → Validator → Publisher, with two human review gates (Gate 1 outline, Gate 2 final).
- **3-pane web workspace** — React 19 + Vite 6 + Zustand + Tailwind 4. Launcher, live pipeline panel, editor, validation/sources/history tabs, Gate modals, PublishKit.
- **Real-time SSE streaming** — pipeline progress streamed to the browser, with per-section "writing → done" progress during Generation.
- **4 parallel Librarian subagents** — official docs / GitHub / English blogs / Korean blogs research via Claude CLI WebSearch & WebFetch.
- **Validator with 30 checks** — STYLE.md format + SEO/AEO/GEO + Oracle semantic critique, with up to 2 reflection retries.
- **9 blog formats** — Concept, Tutorial, Comparison, Troubleshooting, Architecture, Review, Trend, Case Study, Best Practices, with auto-recommendation.
- **$0 cost design** — runs on a Claude Max subscription only; no external LLM / image / search APIs. Mermaid CLI for diagrams.
- **Infrastructure** — Docker Compose, GitHub Actions CI (3-job), Alembic migrations, SQLite runtime store, rate limiting, graceful shutdown.

### Fixed
- 6 P0 stability bugs (Phase 1 hardening).
- SQLite `database is locked` resolved via WAL mode.
- PublishKit image URL double-prefix and automatic HTML conversion.
- Claude CLI subprocess NDJSON parsing (`--verbose` flag).

### Changed
- Test suite established: pytest (600) + Vitest (369) + Playwright, 88% backend coverage.
- README fully revamped (banner, demo GIF, screenshots, docs).

---

## KR v0.1.0 — 최초 MVP 릴리스: 6단계 파이프라인 + 웹 플랫폼

> 릴리스 날짜: 2026-05-26

### 추가
- **6단계 자동화 파이프라인** — Router → Researcher → Outliner → Generator → Validator → Publisher, 사람이 검수하는 두 개의 게이트(Gate 1 아웃라인, Gate 2 최종) 포함.
- **3-pane 웹 워크스페이스** — React 19 + Vite 6 + Zustand + Tailwind 4. Launcher, 실시간 파이프라인 패널, 에디터, 검증/자료/히스토리 탭, Gate 모달, PublishKit.
- **실시간 SSE 스트리밍** — 파이프라인 진행 상황을 브라우저로 스트리밍, Generator 단계에서 섹션별 "작성 중 → 완료" 진행률 표시.
- **4개 병렬 Librarian 서브에이전트** — 공식문서 / GitHub / 영문블로그 / 한글블로그를 Claude CLI WebSearch·WebFetch로 자료조사.
- **30항목 Validator** — STYLE.md 양식 + SEO/AEO/GEO + Oracle 의미 비평, 최대 2회 reflection 재작성.
- **9가지 블로그 포맷** — Concept, Tutorial, Comparison, Troubleshooting, Architecture, Review, Trend, Case Study, Best Practices, 자동 추천 지원.
- **비용 $0 설계** — Claude Max 구독만으로 동작, 외부 LLM/이미지/검색 API 미사용. 다이어그램은 Mermaid CLI.
- **인프라** — Docker Compose, GitHub Actions CI(3-job), Alembic 마이그레이션, SQLite 런타임 저장, rate limiting, graceful shutdown.

### 수정
- P0 안정성 버그 6건 수정 (Phase 1 안정화).
- SQLite `database is locked` 오류를 WAL 모드로 해결.
- PublishKit 이미지 URL 이중 prefix 및 HTML 자동 변환 수정.
- Claude CLI subprocess NDJSON 파싱(`--verbose` 플래그) 수정.

### 변경
- 테스트 스위트 구축: pytest(600) + Vitest(369) + Playwright, 백엔드 커버리지 88%.
- README 전면 개편 (배너, 데모 GIF, 스크린샷, 문서).
