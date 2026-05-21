# CLAUDE.md — Claude Code 작업 규칙 (blog_ai_agent)

> 이 파일은 Claude Code가 이 프로젝트에서 작업할 때 따라야 할 규칙이다.
> **사용자 글로벌 규칙(`~/.claude/CLAUDE.md`)을 상속하며, 이 프로젝트만의 특수 규칙을 추가**한다.

---

## 0. 우선순위

```
프로젝트 CLAUDE.md (이 파일)  >  글로벌 ~/.claude/CLAUDE.md  >  Claude Code 기본 동작
```

이 파일과 글로벌 규칙이 충돌하면 **이 파일이 우선**. 단 보안/데이터 손실 위험 작업은 안전 원칙 최우선.

---

## 1. 프로젝트 정체성

- **목적**: 한국어 기술 블로그(Tistory `jaylenhan.tistory.com`) 작성 자동화 **웹 플랫폼**
- **형태**: React + Vite 프론트엔드 + FastAPI 백엔드 + Claude Code CLI subprocess
- **운영**: 1인 (Jaylen H)
- **타겟 양식**: [AI의 정석] 표준 — `docs/style-guide/blog-style.md` **100% 준수**
- **언어**: 모든 사용자 소통 / 커밋 / 문서 = **한국어**
- **비용 제약**: Claude Max 구독 이외 추가 비용 $0. 외부 LLM/이미지 API 사용 금지

---

## 2. Git 워크플로 (GitHub Flow 엄수)

사용자 글로벌 규칙 그대로 적용:

```
main      ← 안정 버전. 배포 준비 완료 시에만 dev → main 머지
dev       ← 개발 통합. 모든 feature가 여기로 머지
feature/* ← 기능 단위 일회용 브랜치
fix/*     ← 버그 수정
docs/*    ← 문서 작업
chore/*   ← 빌드/도구/설정
```

### 절대 규칙 (위반 시 즉시 중단)

1. **dev에서 직접 코드 수정 금지**. 한 글자라도 `feature/` 또는 `fix/` 브랜치 생성 후 작업
2. **`git push` / `git pull` / `git merge` / `git rebase` / `git tag` / 강제 삭제는 반드시 사용자 승인 후 실행**
3. **커밋 전 사용자에게 보고** → "이대로 커밋할까요?" 물어보고 응답 받기 전엔 커밋 안 함
4. **`--no-verify` / `--force` / `--force-with-lease` 사용 금지**
5. **Co-Authored-By 절대 추가 금지** — Claude가 작성했다는 표시 일체 X
6. **"Generated with Claude Code" 같은 푸터 금지**

### 커밋 메시지 형식 (한국어)

```
<prefix>: <50자 이내 한국어 제목>

<본문 — 무엇을 왜 변경했는지. 줄당 72자 권장>
```

**prefix**: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `style`, `hotfix`

---

## 3. 디렉토리 규칙

### 코드 작업 디렉토리

```
backend/                        ← FastAPI 백엔드 (Python, uv)
├── app/                        ← 애플리케이션 코드
│   ├── main.py                 ← FastAPI 진입점
│   ├── api/                    ← API 라우터
│   ├── pipeline/               ← 6 Stage 파이프라인
│   ├── models/                 ← Pydantic 모델
│   └── services/               ← 비즈니스 로직
├── tests/                      ← 백엔드 테스트
└── pyproject.toml              ← uv 프로젝트 설정

frontend/                       ← React + Vite 프론트엔드
├── src/                        ← 소스 코드
│   ├── components/             ← 3-pane 워크스페이스 컴포넌트
│   ├── hooks/                  ← 커스텀 훅
│   ├── stores/                 ← 상태 관리 (Zustand)
│   └── styles/                 ← 디자인 토큰 + CSS
├── public/                     ← 정적 자산
└── package.json                ← Node 프로젝트 설정

docs/                           ← 기획·설계 문서 (옵시디언 vault)
```

### 글 생성 작업 공간 (런타임)

각 블로그 글 생성마다 자동 디렉토리 생성:

```
.sisyphus/blog/<YYYY-MM-DD>_<topic-slug>/
├── 00_plan.json
├── references/*.md
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

- `.sisyphus/` 는 **`.gitignore`에 포함** (생성 산출물은 커밋 안 함)
- 베스트 케이스 1-2건은 `docs/examples/` 에 정리해서 커밋 (포트폴리오 가치)

---

## 4. 6 Stage 파이프라인 (핵심)

| Stage | 이름 | 역할 |
|-------|------|------|
| 1 | **Router** | 주제 분석, 카테고리 결정, SEO 키워드 계획 |
| 2 | **Researcher** | 4 Librarian 병렬 자료조사 (WebSearch/WebFetch) |
| 3 | **Outliner** | 아웃라인 생성 → **Gate 1** (사용자 검수) |
| 4 | **Generator** | 본문 작성 + 다이어그램/썸네일 생성 |
| 5 | **Validator** | 14+8항목 양식 검증 + oracle → **Gate 2** (사용자 검수) |
| 6 | **Publisher** | Tistory Playwright 배포 |

상세는 `docs/05-architecture/pipeline-stages.md` 참조.

---

## 5. 양식 규칙 (이 프로젝트의 핵심 룰)

블로그 글 생성 시 **반드시 `docs/style-guide/blog-style.md`를 100% 준수**한다.

핵심 요약:
- 톤: 격식체 100% (`~합니다`, `~입니다`)
- 구조: 7~9 대섹션, 1. 들어가며 ~ 마치며
- 분량: 6,000~8,000자 (표준) / 10,000~13,000자 (장문) / 15,000자+ (초장문)
- 표: HTML `<table>` 태그 필수 (마크다운 파이프 X)
- SEO + AEO + GEO 3대 최적화 체크리스트 통과
- FAQ 섹션 / 참고 자료 섹션 **제외**

**위반 시 Validator가 강제 재작성 (Reflection 최대 2회)**.

---

## 6. Python 환경

- **항상 `uv` 사용**. `pip` / `venv` / `poetry` / `conda` 금지
- `pyproject.toml` 사용, `requirements.txt` 금지
- 새 패키지 추가 시 반드시 사용자에게 보고 + 보안 점검

---

## 7. 보안 베이스라인

### 시크릿 관리
- `.env`는 `.gitignore` 필수. `.env.example`만 커밋
- 코드/주석/문서에 하드코딩된 API 키 발견 시 **즉시 사용자에게 알림 + 작업 중단**
- 커밋 전 시크릿 패턴 자가 점검

### Tistory 자동화 보안
- **카카오 OAuth 자동화 시도 금지**. 반드시 사용자 수동 로그인 + 세션 유지 패턴
- 로그인 정보를 환경변수에도 저장 금지
- Playwright `headless=False`로 사용자가 직접 보면서 진행

---

## 8. 외부 의존성 정책

### ✅ 허용 (모두 무료)

| 도구 | 용도 | 비용 |
|------|------|------|
| Claude Code CLI | 백엔드 subprocess 호출 (Max 구독) | $0 |
| WebSearch / WebFetch | Claude Code 내장 자료조사 | $0 |
| FastAPI | 백엔드 API 서버 | $0 |
| React + Vite | 프론트엔드 | $0 |
| mermaid-cli | 다이어그램 PNG 렌더링 | $0 |
| Playwright | 썸네일 + Tistory 배포 | $0 |
| Pillow (PIL) | 이미지 후처리 | $0 |
| SQLite | 런타임 상태 저장 | $0 |

### ❌ 금지

- OpenAI / Gemini / 기타 유료 LLM API
- DALL-E / FLUX / Midjourney 등 유료 이미지 생성
- Tavily / Exa / Serper 등 유료 검색 API
- Cloudinary / S3 등 유료 호스팅
- 외부 분석 도구 (Datadog, Sentry 등)

새 의존성 추가가 필요하면 **반드시 사용자에게 먼저 묻는다**.

---

## 9. 검수 게이트 정책

| Gate | 위치 | 무엇을 묻는가 | 건너뛸 수 있나 |
|------|------|----------|------------|
| **Gate 1** | Stage 3 (Outliner) 완료 후 | "이 아웃라인으로 본문을 작성할까요?" | `--auto` 플래그 명시 시만 |
| **Gate 2** | Stage 5 (Validator) 완료 후 | "이 최종 글을 Tistory에 게시할까요?" | **절대 X** |

**Claude는 이 게이트를 임의로 건너뛰지 않는다.** 사용자가 명시적 옵션을 줘야만.

---

## 10. 작업 시작 시 체크리스트

- [ ] 현재 브랜치 확인 (`git status`) — `dev`나 `main`이면 새 브랜치 생성 제안
- [ ] `docs/08-milestones.md` 확인 — 현재 어느 Phase인지
- [ ] 새 의존성 필요한가? → 사용자 승인 먼저
- [ ] 사용자 글로벌 규칙 + 이 파일 충돌 없는지 재확인

---

## 11. 자주 발생할 만한 상황 대응

| 상황 | 대응 |
|------|------|
| "그냥 빨리 해줘" | 검수 게이트는 건너뛰지 않음. 검수 멘트만 압축 |
| STYLE.md 위반 글 생성됨 | 사용자에게 보고 + 재작성 |
| Tistory 에디터 셀렉터 깨짐 | 임의로 다른 셀렉터 시도 X. 사용자에게 보고 |
| 글 길이 < 1,000줄 | 사용자에게 어느 섹션을 더 깊게 다룰지 선택지 제시 |
| 자료조사에서 정보 부족 | 추측으로 채우지 X. 사용자에게 보고 |

---

## 12. 위반 시 행동

이 규칙을 어겼다는 것을 **인지한 즉시 사용자에게 보고** 후 가능한 자가 정정.
사용자가 명시적으로 예외를 지시한 경우만 규칙 우회 가능.

---

## 13. 참고 문서

- `~/.claude/CLAUDE.md` — 사용자 글로벌 규칙
- [`AGENTS.md`](AGENTS.md) — 에이전트 운용 가이드
- [`docs/style-guide/blog-style.md`](docs/style-guide/blog-style.md) — 블로그 양식 표준
- [`docs/05-architecture/`](docs/05-architecture/) — 시스템 아키텍처
- [`docs/08-milestones.md`](docs/08-milestones.md) — 마일스톤
