# 현재 상태 (2026-05-23)

## 전체 진행률

| 영역 | 상태 | 상세 |
|------|------|------|
| 백엔드 파이프라인 | ✅ 완료 | 6 Stage + 2 Gate 전체 구현 (Router→Researcher→Outliner→Gate1→Generator→Validator→Gate2→Publisher) |
| 백엔드 테스트 | ✅ 502건, 90% | pytest + pytest-cov (34 테스트 파일) |
| 프론트엔드 컴포넌트 | ✅ 33개 | 3-pane 워크스페이스, Launcher, Gate 모달, PublishKit 등 |
| 프론트엔드 테스트 | ✅ 344건 (32파일) | 컴포넌트 19 + 훅 5 + 스토어 6 + API 2 |
| 프론트엔드 스토어/훅 | ✅ 완료 | Zustand 6 스토어, 커스텀 훅 5개 |
| API 엔드포인트 | ✅ 38개 | articles 15 + pipeline 12 + settings 6 + formats 3 + health 2 |
| SSE 실시간 스트리밍 | ✅ 완료 | REST → SSE 전환, 재연결 로직 포함 |
| Zod 유효성 검증 | ✅ 완료 | API 응답 스키마 전체 적용 |
| E2E 테스트 | ✅ 16건 | Playwright 5 시나리오 (앱 로딩, SSE 플로우, 사이드바, 에러 처리, 상태 복원) |
| Docker | ✅ 완료 | docker-compose.yml (backend + frontend + healthcheck) |
| CI/CD | ✅ 완료 | GitHub Actions 3-job 파이프라인 (backend-test → frontend-build → frontend-e2e) |
| Rate Limiting | ✅ 완료 | API 미들웨어 적용 |
| Graceful Shutdown | ✅ 완료 | 시그널 핸들링 |
| Health Check | ✅ 완료 | Claude CLI + mmdc + Obsidian vault 상세 점검 |
| Code Splitting | ✅ 완료 | 561KB → 213KB (메인 번들), highlight.js 별도 청크 분리 |
| 환경 분리 | ✅ 완료 | .env.development / .env.production |

## 테스트 요약

| 영역 | 테스트 수 | 커버리지 | 도구 |
|------|----------|---------|------|
| 백엔드 유닛/통합 | 502건 | 90% | pytest + pytest-cov |
| 프론트엔드 유닛 | 344건 | — | Vitest + Testing Library |
| E2E | 16건 | — | Playwright (5 시나리오 파일) |
| **합계** | **862건** | — | — |

## 최근 작업

- CI/CD 전체 안정화 (백엔드 mermaid mock, highlight.js 의존성, E2E formats mock)
- E2E 테스트 안정화 — mockFormatsAPI 헬퍼 추가, sidebar mock 데이터 보정
- README.md 전면 개편 (SVG 배너, 데모 GIF, 파이프라인 다이어그램, 스크린샷)
- CONTRIBUTING.md 신규 작성
- CI 린트 에러 해소 (ruff unused imports, pnpm 버전 고정)
- ESLint `no-explicit-any` 16건 전체 수정
- 컴포넌트 테스트 83건 추가 (10개 신규 테스트 파일)
- 백엔드 포맷 레지스트리 테스트 27건 추가
- SSE 재연결 방어 로직 개선 (optional chaining)
- Vite 빌드 최적화 (markdown 청크 516KB → 338KB)

## Phase 완료 현황

| Phase | 문서 | 상태 | 마일스톤 |
|-------|------|------|----------|
| Phase 0 | `00-elevator-pitch.md` | ✅ 완료 | M1 |
| Phase 1 | `01-problem-statement.md` | ✅ 완료 | M1 |
| Phase 2 | `02-benchmark.md` | ✅ 완료 | M1 |
| Phase 3 | `03-team-and-roles.md` | ✅ 완료 | M1 |
| Phase 4 | `04-requirements.md` | ✅ 완료 | M1 |
| Phase 5 | `05-architecture/` (7문서) | ✅ 완료 | M1 |
| Phase 6 | `06-ux-design.md` | ✅ 완료 | M2 |
| Phase 7 | `07-project-setup.md` | ✅ 완료 | M2 |
| Phase 8 | `08-milestones.md` | ✅ 완료 | M2 |
| Phase 9~16 | 파이프라인 코어 ~ QA/배포 | ✅ 완료 | M3~M6 |
| Phase 17~22 | 프론트엔드 구현 + 테스트 보강 | ✅ 완료 | M6 |

## 미구현 / 향후 과제

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| 주제 큐 (예약 발행) | 중 | M8 |
| 발행 후 Analytics | 낮음 | M8 |
| Playwright 반자동 발행 | 중 | M8 |
| HTML+CSS 썸네일 자동화 | 낮음 | M8 |
| Tistory 자동 로그인 | 금지 | 보안 정책상 수동 로그인만 허용 |
| 실제 Claude CLI E2E | 수동 | docs/09-manual-test-scenarios.md 참조 |
| v0.1.0 태깅 | 대기 | main 머지 완료, 태그 생성 예정 |
