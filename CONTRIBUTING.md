# 기여 가이드

Blog AI Agent에 관심을 가져 주셔서 감사합니다. 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

---

## 개발 환경 셋업

### 사전 요구사항

- Python 3.12+ / [uv](https://docs.astral.sh/uv/)
- Node.js 22+ / [pnpm](https://pnpm.io/)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (Max 구독 인증 완료)
- (선택) [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) — 다이어그램 렌더링용

### 설치

```bash
git clone https://github.com/JaylenAI/blog_ai_agent.git
cd blog_ai_agent

# 백엔드
cd backend
cp ../.env.example .env
uv sync --all-extras --all-groups

# 프론트엔드
cd ../frontend
pnpm install
```

---

## 브랜치 전략

GitHub Flow를 사용합니다.

```
main      ← 안정 릴리스 전용
dev       ← 개발 통합 브랜치
feature/* ← 새 기능 (dev에서 분기)
fix/*     ← 버그 수정
docs/*    ← 문서 작업
chore/*   ← 빌드/도구/설정
```

### 규칙

1. **`dev`에서 직접 코드 수정 금지** — 반드시 브랜치를 생성합니다
2. `main`에 직접 커밋/push 금지 — `dev → main` 머지는 릴리스 시에만
3. feature 브랜치는 `dev`에서 분기하고, 완료 후 `dev`로 squash merge합니다
4. 머지 전 테스트, 린트, 타입체크를 모두 통과해야 합니다

---

## 커밋 메시지

**한국어**로 작성하며, conventional commit prefix를 사용합니다.

```
<prefix>: <제목 — 50자 이내>

<본문 — 무엇을 왜 변경했는지>
```

| prefix | 용도 |
|--------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 |
| `test` | 테스트 추가/수정 |
| `refactor` | 리팩토링 |
| `chore` | 빌드/설정 |
| `perf` | 성능 개선 |

---

## 테스트

PR을 보내기 전에 모든 테스트가 통과하는지 확인해 주세요.

```bash
# 백엔드 — 502 tests, 90% coverage
cd backend && uv run pytest tests/ -x -q

# 프론트엔드 — 344 tests
cd frontend && pnpm test

# E2E — 16 scenarios
cd frontend && pnpm test:e2e

# 린트 + 타입체크
cd backend && uv run ruff check app/ tests/
cd frontend && pnpm lint && pnpm typecheck
```

---

## 코드 스타일

### Python (백엔드)

- 포매터/린터: [Ruff](https://docs.astral.sh/ruff/)
- 비동기: `async/await` 기반 (SQLAlchemy async, aiosqlite)
- 타입 힌트 필수

### TypeScript (프론트엔드)

- `strict: true`
- Prettier + ESLint
- Zustand 상태 관리 — 불변성 패턴 준수
- zod 런타임 검증

---

## PR 가이드라인

1. **하나의 PR = 하나의 목적.** 기능 추가와 리팩토링을 섞지 않습니다
2. PR 제목은 커밋 prefix 형식을 따릅니다 (예: `feat: 검색 기능 추가`)
3. 테스트가 포함되어야 합니다 — 새 기능은 유닛 테스트 필수
4. CI(GitHub Actions)가 통과해야 머지 가능합니다

---

## 파이프라인 아키텍처

기여 시 6단계 파이프라인 구조를 이해하면 도움이 됩니다.

```
Router → Researcher → Outliner → [Gate 1] → Generator → Validator → [Gate 2] → Publisher
```

- 각 Stage는 `backend/app/pipeline/stages/`에 독립 모듈로 구현되어 있습니다
- Gate 1은 설정으로 건너뛸 수 있지만, **Gate 2는 반드시 사람의 승인이 필요합니다**
- 상세 아키텍처는 [`docs/05-architecture/`](docs/05-architecture/)를 참고하세요

---

## 의존성 정책

- **외부 유료 API 사용 금지** — Claude Max 구독 이외 추가 비용 $0
- Python 의존성: `uv add` 사용 (pip/poetry 금지)
- Node 의존성: `pnpm add` 사용
- 새 의존성 추가 시 PR 설명에 사유를 명시해 주세요

---

## 질문이 있으시다면

이슈를 생성하거나, [jaylenhan.tistory.com](https://jaylenhan.tistory.com)을 방문해 주세요.

---

MIT &copy; 2026 Jaylen H
