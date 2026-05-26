# 현재 상태 (2026-05-26)

## 전체 진행률

| 영역 | 상태 | 상세 |
|------|------|------|
| 백엔드 파이프라인 | ✅ 완료 | 6 Stage + 2 Gate 전체 구현 (Router→Researcher→Outliner→Gate1→Generator→Validator→Gate2→Publisher) |
| 백엔드 테스트 | ✅ 600건, 88% | pytest + pytest-cov (unit + integration) |
| 프론트엔드 컴포넌트 | ✅ 33개 | 3-pane 워크스페이스, Launcher, Gate 모달, PublishKit 등 |
| 프론트엔드 테스트 | ✅ 369건 | Vitest + Testing Library |
| 프론트엔드 스토어/훅 | ✅ 완료 | Zustand 6 스토어, 커스텀 훅 5개 |
| API 엔드포인트 | ✅ 38개 | articles 15 + pipeline 12 + settings 6 + formats 3 + health 2 |
| SSE 실시간 스트리밍 | ✅ 완료 | REST → SSE 전환, 모듈 레벨 싱글톤 연결 관리, 섹션별 실시간 진행률 |
| Zod 유효성 검증 | ✅ 완료 | API 응답 스키마 전체 적용 |
| Docker | ✅ 완료 | docker-compose.yml (backend + frontend + healthcheck) |
| CI/CD | ✅ 완료 | GitHub Actions 3-job 파이프라인 (backend-test → frontend-build → frontend-e2e) |
| Rate Limiting | ✅ 완료 | Pure ASGI 미들웨어 (BaseHTTPMiddleware 탈피) |
| Graceful Shutdown | ✅ 완료 | 시그널 핸들링 |
| Health Check | ✅ 완료 | Claude CLI + mmdc + Obsidian vault 상세 점검 |
| 환경 분리 | ✅ 완료 | .env.development / .env.production |

## 테스트 요약

| 영역 | 테스트 수 | 커버리지 | 도구 |
|------|----------|---------|------|
| 백엔드 유닛/통합 | 600건 | 88% | pytest + pytest-cov |
| 프론트엔드 유닛 | 369건 | — | Vitest + Testing Library |
| E2E | — | — | Playwright |

## 최근 작업 (2026-05-26)

### SSE 연결 끊김 근본 원인 해결
- **근본 원인**: `usePipelineSSE` 훅이 GateModal 내부에서 호출됨 → Gate 1 승인 시 `closeGateModal()` → 모달 unmount → cleanup effect가 `abortRef.current?.abort()` 실행 → SSE 연결 즉사
- **해결**: `useRef<AbortController>` → 모듈 레벨 싱글톤 `_currentAbort` 변수로 교체, unmount cleanup effect 제거
- **결과**: Gate 1 승인 → Generator → Validator → Gate 2까지 전체 파이프라인 정상 동작 확인

### 미들웨어 Pure ASGI 전환
- **RequestLoggerMiddleware**: `BaseHTTPMiddleware` → Pure ASGI (SSE 응답 버퍼링 방지)
- **RateLimiterMiddleware**: `BaseHTTPMiddleware` → Pure ASGI (동일 이유)

### SSE keepalive 및 프록시 타임아웃 해소
- **백엔드**: `_sse_from_queue`에 15초 keepalive comment 추가
- **프론트엔드**: Vite proxy `timeout: 0`, `proxyTimeout: 0` 설정

### Editor 하드코딩 제거
- **이전**: `completedSections`를 존재하지 않는 `stage_complete:generator` 이벤트에서 계산 → 항상 빈 Set → 하드코딩 fallback 발동
- **이후**: `sectionProgress` Zustand store에서 직접 읽어 실시간 반영

### Generator 섹션별 실시간 진행률 구현
- **SectionWriter** 신규 모듈: 섹션 단위 Claude CLI 호출 + 품질 기반 재시도
- **Generator 리팩터링**: 단일 모놀리식 호출 → 섹션별 호출로 전환
- **stage_progress 이벤트**: Generator가 "작성 중"/"완료" 이벤트를 섹션마다 emit
- **Orchestrator 진행률 드레인**: asyncio.Queue 기반 실시간 이벤트 전달 루프
- **프론트엔드 실시간 UI**: 프로그레스 바 + 현재 섹션명 + 완료 카운트 표시

### Researcher 개선
- **WebSearch/WebFetch 도구 활성화**: LibrarianSubagent에 `allowed_tools=["WebSearch", "WebFetch"]` 추가
- **주제 적합성 프롬프트 강화**: 각 Librarian에 관련성 규칙 + 검색 쿼리 힌트 추가

### 테스트 보강
- `test_section_writer.py` 신규 (8건): 성공/짧은 내용 재시도/전송 오류 즉시 실패
- `test_generator_stage.py` 전면 리팩터링: SectionWriter mock 기반
- `test_generator_progress_e2e.py` 신규 (6건): Gate 1 승인 → Generator 실시간 이벤트 흐름 E2E
- `test_pipeline_orchestrator.py` 업데이트: ProgressCallback 시그니처 대응

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
