# AGENTS.md — 에이전트 운용 가이드

> 이 프로젝트에서 Claude Code의 Agent/Subagent, MCP 도구를 어떻게 활용하는지 정리한다.
> 백엔드(FastAPI)가 Claude Code CLI를 subprocess로 호출하여 파이프라인을 실행한다.

---

## 1. 아키텍처 개요

```
사용자 (브라우저)
  ↕ HTTP/SSE
FastAPI 백엔드
  ↕ subprocess
Claude Code CLI (Max 구독)
  ↕ Agent tool
Subagent (Librarian, Oracle 등)
```

- **추가 API 키 불필요** — Claude Max 구독에 포함된 Claude Code CLI 사용
- **SSE(Server-Sent Events)** — 파이프라인 진행 상황을 프론트엔드에 실시간 스트리밍

---

## 2. 6 Stage 파이프라인 에이전트 매핑

| Stage | 이름 | 실행 방식 | Subagent |
|-------|------|----------|----------|
| 1 | Router | Orchestrator 직접 | - |
| 2 | Researcher | Subagent × 4 병렬 | librarian-official, librarian-github, librarian-blog-en, librarian-blog-kr |
| 3 | Outliner | Orchestrator 직접 | - |
| - | **Gate 1** | **사용자 검수** (웹 UI) | - |
| 4 | Generator | Orchestrator 직접 | - (이미지는 병렬 처리) |
| 5 | Validator | Python 자동 검증 + Subagent | oracle (양식 위반 심각 시) |
| - | **Gate 2** | **사용자 검수** (웹 UI) | - |
| 6 | Publisher | Orchestrator 직접 | - (Playwright) |

---

## 3. Subagent 상세

### 3-1. 4 Librarian Subagent (Stage 2)

Stage 2 Researcher에서 **4개 병렬** 호출:

| Subagent | 검색 영역 | 도구 |
|----------|----------|------|
| `librarian-official` | 공식 문서, 논문, arXiv | WebSearch + WebFetch |
| `librarian-github` | GitHub 저장소, 코드 사례 | WebSearch + WebFetch |
| `librarian-blog-en` | 영문 기술 블로그 (Medium, 공식 엔지니어링 블로그) | WebSearch + WebFetch |
| `librarian-blog-kr` | 한글 기술 블로그 (네이버 D2, 카카오, tistory) | WebSearch + WebFetch |

**호출 규칙:**
- 4개 모두 `run_in_background=true`로 병렬 실행
- 각 Librarian은 3~5개 자료 수집 → 총 12~20개
- 결과를 Orchestrator가 취합하여 Stage 3에 전달

### 3-2. Oracle Subagent (Stage 5)

- **용도**: 양식 위반이 심각하거나 Validator 자동 검증으로 판단이 어려운 경우
- **선택적 호출**: 모든 글에 호출하지 않음. Validator가 판단
- **절대 cancel하지 않음**

### 3-3. Subagent 프롬프트 규칙

모든 Subagent 호출 시 4개 필드 명시:

```
[CONTEXT]    무엇을 하고 있는지
[GOAL]       이 결과로 무엇을 결정/실행하는지
[DOWNSTREAM] 결과를 어떻게 쓸 건지
[REQUEST]    구체적으로 찾을 것
```

---

## 4. 사용자 입력 3채널

웹 플랫폼에서 사용자는 3가지 방식으로 자료를 제공할 수 있다:

| 채널 | 입력 방식 | 처리 |
|------|----------|------|
| **자동** | 주제만 입력 → Librarian이 WebSearch/WebFetch | 자동 |
| **수동** | 사용자가 URL/텍스트를 직접 붙여넣기 | WebFetch로 본문 추출 |
| **크롤링** | 사용자가 URL 제공 → Playwright로 동적 페이지 크롤링 | 자동 (요청 시) |

---

## 5. MCP 도구

| 도구 | 용도 | 활성화 |
|------|------|--------|
| **WebSearch** (내장) | 일반 자료조사, 최신 동향 | 기본 |
| **WebFetch** (내장) | 특정 URL 본문 추출 | 기본 |
| **Playwright** | 브라우저 자동화 (썸네일 + Tistory) | Python 패키지 |

---

## 6. 백엔드 → Claude Code CLI 호출 패턴

FastAPI 백엔드가 Claude Code CLI를 subprocess로 호출하여 파이프라인을 실행한다.

```python
import subprocess
import json

async def run_claude_pipeline(topic: str, options: dict) -> AsyncGenerator:
    process = subprocess.Popen(
        ["claude", "-p", prompt, "--output-format", "stream-json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for line in process.stdout:
        yield json.loads(line)
```

- `--output-format stream-json` — 실시간 스트리밍
- 결과를 SSE로 프론트엔드에 전달
- Claude Max 구독으로 동작 → 추가 API 비용 $0

---

## 7. Reflection 정책

- Validator(Stage 5)에서 양식 위반 발견 시 **최대 2회 Reflection**
- 2회 후에도 미통과 시 사용자에게 보고 (자동 재시도 중단)
- Gate 2에서 사용자가 직접 판단

---

## 8. 절대 규칙

1. **외부 API 키 사용 금지** — Claude Max 구독 + 무료 도구만
2. **Subagent 결과를 검증 없이 그대로 사용 금지** — 항상 취합·검증 후 사용
3. **Tistory 자동화 시 카카오 OAuth 자동화 금지** — 항상 수동 로그인
4. **Validator 결과 무시 금지** — 양식 위반 잡혔으면 반드시 재작성
5. **Gate 2는 절대 자동 통과 불가** — 게시는 사람이 결정

---

## 9. 참고 문서

- [`CLAUDE.md`](CLAUDE.md) — Claude Code 작업 규칙
- [`docs/style-guide/blog-style.md`](docs/style-guide/blog-style.md) — 블로그 양식 표준
- [`docs/05-architecture/pipeline-stages.md`](docs/05-architecture/pipeline-stages.md) — 6 Stage 상세
- [`docs/05-architecture/research-strategy.md`](docs/05-architecture/research-strategy.md) — 자료조사 전략
- [`docs/05-architecture/validator-design.md`](docs/05-architecture/validator-design.md) — Validator 설계
