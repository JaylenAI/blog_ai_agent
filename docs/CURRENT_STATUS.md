# 현재 상태 (2026-05-21)

## 전체 진행률

| 영역 | 상태 | 상세 |
|------|------|------|
| 6 Stage 파이프라인 | ✅ 100% | Router→Researcher→Outliner→Generator→Validator→Publisher |
| 단위 테스트 | ✅ 285건, 91.59% | pytest + pytest-cov |
| E2E 테스트 | ✅ 9건 | Playwright (앱 로딩, SSE 플로우, 상태 복원) |
| SSE 실시간 스트리밍 | ✅ 완료 | REST → SSE 전환 완료 |
| 페이지 새로고침 복원 | ✅ 완료 | active run 자동 감지 |
| Health Check 상세 | ✅ 완료 | Claude CLI + mmdc + Obsidian vault |
| Docker | ✅ 완료 | docker-compose.yml (backend + frontend) |
| CI/CD | ✅ 완료 | GitHub Actions (test + lint + e2e) |
| 환경 분리 | ✅ 완료 | .env.development / .env.production |
| Code Splitting | ✅ 완료 | 561KB → 213KB (메인 번들) |
| 수동 테스트 시나리오 | ✅ 완료 | docs/09-manual-test-scenarios.md |

## 미구현 / 향후 과제

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| 주제 큐 (예약 발행) | 중 | M8 |
| 발행 후 Analytics | 낮음 | M8 |
| Tistory 자동 로그인 | 금지 | 보안 정책상 수동 로그인만 허용 |
| 실제 Claude CLI E2E | 수동 | docs/09-manual-test-scenarios.md 참조 |
| v0.1.0 태깅 | 대기 | main 머지 시 |

## 최근 완료 Phase

### Phase 7: SSE 실시간 연동 + 상태 복원
- AppShell handleStart → SSE 스트리밍
- approveGate → SSE 스트리밍
- use-restore-pipeline 훅 (페이지 새로고침 복원)
- GET /pipeline/runs/active 엔드포인트
- .env.example 생성

### Phase 8: E2E 테스트 + 수동 테스트
- Playwright 9건 (앱 로딩 4 + SSE 플로우 3 + 상태 복원 2)
- 상세 health check (Claude CLI, mmdc, Obsidian vault)
- 수동 테스트 시나리오 문서 8건

### Phase 9: Docker + CI/CD + 환경 분리
- backend/Dockerfile, frontend/Dockerfile + nginx.conf
- docker-compose.yml (healthcheck 포함)
- .github/workflows/ci.yml (3 jobs)
- React.lazy code splitting

### Phase 10: 최종 QA + 문서
- README 업데이트 (빠른 시작 가이드 추가)
- CURRENT_STATUS.md 작성
