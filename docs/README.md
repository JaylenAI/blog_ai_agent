---
tags:
  - project/blog-ai-agent
  - docs/index
  - phase/all
date: 2026-05-20
created: 2026-05-20
updated: 2026-05-21
aliases:
  - 문서 인덱스
  - Documentation Index
status: active
---

# 📚 Blog AI Agent — Documentation Index

> 이 디렉토리는 [Blog AI Agent](../README.md) 프로젝트의 모든 기획/설계/운영 문서를 담는다. 
> 부록 E의 16 Phase 프로세스를 그대로 매핑했다. 옵시디언 vault로도 작동.

---

## 🗺️ Phase별 문서 매트릭스

| # | 문서 | Phase | 상태 | 우선순위 |
|---|------|-------|------|---------|
| 00 | [00-elevator-pitch.md](00-elevator-pitch.md) | Phase 0 — 아이디어 발굴 + 5기준 평가 | ✅ 완료 | 🔥 |
| 01 | [01-problem-statement.md](01-problem-statement.md) | Phase 1 — 문제 정의 | ✅ 완료 | 🔥 |
| 02 | [02-benchmark.md](02-benchmark.md) | Phase 2 — 시장 조사 / 벤치마크 / SWOT | ✅ 완료 | 🔥 |
| 03 | [03-team-and-roles.md](03-team-and-roles.md) | Phase 3 — 팀 빌딩 (1인 운영) | ✅ 완료 | 🟡 |
| 04 | [04-requirements.md](04-requirements.md) | Phase 4 — MoSCoW 요구사항 + 시나리오 | ✅ 완료 | 🔥 |
| 05 | [05-architecture/](05-architecture/) | Phase 5 — 시스템 설계 (7개 하위 문서) | ✅ 완료 | 🔥 |
| 06 | [06-ux-design.md](06-ux-design.md) | Phase 6 — UX/UI 설계 (3-pane 워크스페이스) | ✅ 완료 | 🟡 |
| 07 | [07-project-setup.md](07-project-setup.md) | Phase 7 — Git/UV/환경 셋업 | ✅ 완료 | 🔥 |
| 08 | [08-milestones.md](08-milestones.md) | Phase 8 — 마일스톤 + Gantt | ✅ 완료 | 🔥 |
| 09 | [09-development-guide.md](09-development-guide.md) | Phase 9 — 개발 가이드 (수직 슬라이스) | 🔄 작성 예정 | 🟡 |
| 10 | [10-qa-test-plan.md](10-qa-test-plan.md) | Phase 10 — QA + 양식 검증 | 🔄 작성 예정 | 🟡 |
| 11 | [11-deployment.md](11-deployment.md) | Phase 11 — Tistory 배포 가이드 | 🔄 작성 예정 | 🟡 |
| 12 | [12-demo-scenarios.md](12-demo-scenarios.md) | Phase 12 — 데모 시나리오 | 🔄 작성 예정 | 🟢 |
| 13 | [13-success-metrics.md](13-success-metrics.md) | Phase 13 — KPI (속도/품질/비용) | 🔄 작성 예정 | 🔥 |
| 14 | [14-documentation-index.md](14-documentation-index.md) | Phase 14 — 산출물 정리 | 🔄 작성 예정 | 🟡 |
| 15 | [15-roadmap.md](15-roadmap.md) | Phase 15 — 추후 방향성 | 🔄 작성 예정 | 🟡 |
| 16 | [16-retrospective.md](16-retrospective.md) | Phase 16 — 회고 템플릿 | 🟢 사용 후 채움 | 🟢 |

**범례**: 🔥 필수 / 🟡 중요 / 🟢 권장 · ✅ 완료 / 🔄 진행 중 / ⏳ 예정

---

## 🧭 카테고리별 문서

부록 E 16 Phase를 의미상 4개 카테고리로 묶으면 다음과 같다.

### 🤔 WHY — 왜 만드는가?
- [[00-elevator-pitch]] · 한 줄 정의 + 5기준 점수표
- [[01-problem-statement]] · As-Is / Pain / To-Be
- [[02-benchmark]] · 경쟁 분석 + SWOT + 차별점

### 🏗️ HOW — 어떻게 만드는가?
- [[03-team-and-roles]] · 역할 분담 (1인이지만 모자 분리)
- [[04-requirements]] · MoSCoW + 비기능 + 사용자 시나리오
- [[05-architecture/README|05-architecture]] · 시스템 설계 (7개 하위)
- [[06-ux-design]] · CLI 상호작용 흐름
- [[07-project-setup]] · 환경 셋업

### 🔨 BUILD — 어떻게 짓는가?
- [[08-milestones]] · 6 Phase 마일스톤 + Gantt
- [[09-development-guide]] · 수직 슬라이스 + 커밋 컨벤션
- [[10-qa-test-plan]] · 양식 검증 + 자동/수동 테스트
- [[11-deployment]] · Tistory Playwright 배포

### 📊 MEASURE — 어떻게 검증/개선하는가?
- [[12-demo-scenarios]] · 데모용 주제 3개
- [[13-success-metrics]] · 속도/품질/비용 KPI
- [[14-documentation-index]] · 산출물 정리
- [[15-roadmap]] · 단기/중기/장기 확장
- [[16-retrospective]] · 4L 회고 (사용 후)

---

## 📐 표준 / 결정 문서

핵심 양식과 의사결정을 별도 디렉토리로 관리.

### 🎨 [style-guide/](style-guide/) — 양식 표준 (가장 중요)

| 문서 | 내용 | 상태 |
|------|------|------|
| [blog-style.md](style-guide/blog-style.md) | **STYLE.md 풀버전** + SEO/AEO/GEO 3대 최적화 통합. Validator 기준 | ✅ 완료 |
| tone-guide.md | 한국어 격식체 톤 가이드 + 금지 표현 | 🔄 작성 예정 |
| thumbnail-design.md | HTML/CSS 썸네일 디자인 시스템 | 🔄 작성 예정 |
| diagram-conventions.md | Mermaid 스타일 규칙 (색상, 폰트, 레이아웃) | 🔄 작성 예정 |
| seo-checklist.md | SEO/AEO/GEO 체크리스트 (Validator 참조용) | 🔄 작성 예정 |

### ⚖️ [adr/](adr/) — Architecture Decision Records

| ADR | 결정 사항 | 상태 |
|-----|--------|------|
| 001 | Claude Code CLI subprocess 채택 (vs LangGraph/CrewAI) | 🔄 작성 예정 |
| 002 | Tistory 유지 + Velog 백업 (배포 정책) | 🔄 작성 예정 |
| 003 | Mermaid + HTML 썸네일 채택 (vs DALL-E/FLUX) | 🔄 작성 예정 |
| 004 | WebSearch 내장만 사용 (vs Tavily) | 🔄 작성 예정 |
| 005 | HTML/CSS + Playwright 썸네일 방식 | 🔄 작성 예정 |

### 🗣️ meetings/ — 의사결정 회의록

| 회의록 | 주제 | 상태 |
|--------|------|------|
| 2026-05-20-kickoff.md | Kickoff — 전체 기획 + 핵심 결정 | 🔄 작성 예정 |

---

## 🌐 옵시디언 vault로 사용하는 법

### 1. Import 방법

```
옵시디언 → "Open another vault" → "Open folder as vault"
경로: ~/Desktop/blog_ai_agent/docs/
```

### 2. 진입점

[`_index.md`](_index.md) 가 vault의 홈. 옵시디언 그래프 뷰에서 가장 큰 노드.

### 3. 위키링크 동작

모든 문서에 다음 형태로 링크:
```markdown
[[00-elevator-pitch|🎯 엘리베이터 피치]]
[[05-architecture/system-overview|시스템 개요]]
```

### 4. 태그 규칙 (사용자 글로벌 컨벤션 준수)

```yaml
tags:
  - project/blog-ai-agent     # 항상
  - phase/0 ~ phase/16        # 해당 Phase
  - docs/{type}               # docs 분류
  - style-guide               # 양식 관련 시
  - adr                       # 의사결정 시
```

### 5. YAML frontmatter 표준

모든 `.md` 파일 상단에:
```yaml
---
tags: [...]
date: YYYY-MM-DD
created: YYYY-MM-DD
updated: YYYY-MM-DD
aliases:
  - 한국어 별칭
status: active | draft | archived
related:
  - "[[...]]"
---
```

---

## 🔍 빠른 검색

| 찾는 것 | 가장 빠른 경로 |
|--------|------------|
| 양식 한 줄 규칙 | [style-guide/blog-style.md](style-guide/blog-style.md) |
| 6 Stage 파이프라인 | [05-architecture/pipeline-stages.md](05-architecture/pipeline-stages.md) |
| 시스템 설계 개요 | [05-architecture/README.md](05-architecture/README.md) |
| 다음 작업은? | [08-milestones.md](08-milestones.md) |
| 프로젝트 진입점 | [../README.md](../README.md) |

---

## 🛠️ 문서 작성 표준

이 docs/ 안의 모든 문서는 다음을 따른다:

1. **YAML frontmatter 필수** (옵시디언 호환)
2. **H1 = 문서 제목** (한 개만)
3. **부록 E의 Phase 표제 양식 따름** (`💡 ... ⚠️ ...` 박스 사용)
4. **Mermaid 다이어그램은 인라인** (별도 이미지 X — 버전 관리 어려움)
5. **위키링크 우선** (절대 경로 링크보다 `[[...]]` 형태)
6. **변경 시 `updated` 필드 갱신**
7. **상태 변경 시 `status` 필드 갱신** (`draft` → `active` → `archived`)
