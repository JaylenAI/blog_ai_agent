# 수동 테스트 시나리오

> E2E 자동화가 어려운 항목에 대한 수동 테스트 체크리스트.
> 실제 Claude CLI와 Tistory/Obsidian 연동이 필요한 시나리오.

---

## 1. 파이프라인 전체 플로우 (Happy Path)

### 사전 조건
- 백엔드 서버 실행 중 (`uv run uvicorn app.main:app --reload`)
- 프론트엔드 dev 서버 실행 중 (`pnpm dev`)
- Claude CLI 인증 완료 (`claude --version`으로 확인)

### 테스트 절차

1. 브라우저에서 `http://localhost:5173` 접속
2. 주제 입력란에 "Python 비동기 프로그래밍 입문" 입력
3. "생성 시작" 클릭
4. PipelineProgress 바가 실시간으로 진행되는지 확인
   - [ ] Router → Researcher → Outliner 순서대로 진행
   - [ ] 각 단계 시작/완료 이벤트가 표시됨
5. Gate 1 모달이 표시되는지 확인
   - [ ] 아웃라인 내용이 표시됨
   - [ ] "본문 생성 시작" 버튼 활성화
6. "본문 생성 시작" 클릭
7. Generator → Validator 단계 진행 확인
8. Gate 2 모달 표시 확인
   - [ ] 최종 본문이 에디터에 표시됨
   - [ ] Validator 결과 요약 확인 가능
9. "발행 준비 승인" 클릭
10. Publisher 단계 완료 확인

### 예상 결과
- `.sisyphus/blog/` 하위에 작업 디렉토리 생성됨
- `final.md`, `tistory.html`, `meta.json` 파일 생성됨
- 전체 소요시간: 5~15분 (Claude CLI 응답 속도에 따라)

---

## 2. Gate 거부 플로우

1. 시나리오 1과 동일하게 Gate 1까지 진행
2. "거부" 버튼 클릭
3. [ ] 파이프라인이 "idle" 상태로 돌아감
4. [ ] 에러 없이 새 주제로 다시 시작 가능

---

## 3. 페이지 새로고침 복원

1. 파이프라인 실행 중 Gate 1에서 멈춘 상태에서 브라우저 새로고침 (F5)
2. [ ] Gate 1 모달이 자동으로 다시 표시됨
3. [ ] 아웃라인 내용이 정상 표시됨
4. "본문 생성 시작" 클릭 후 정상 진행 확인

---

## 4. Obsidian Vault 연동

### 사전 조건
- `.env`에 `OBSIDIAN_VAULT_PATH=/path/to/your/vault` 설정
- 해당 경로가 실제 Obsidian vault 디렉토리

### 테스트 절차

1. 파이프라인 전체 플로우 완료 (시나리오 1)
2. Obsidian vault 디렉토리 확인
   - [ ] `<글 제목>.md` 파일이 생성됨
   - [ ] YAML frontmatter에 `tags`, `date`, `status` 포함
   - [ ] `blog/published` 태그 포함
   - [ ] 본문 내용이 정확히 일치

---

## 5. Claude CLI 장애 시나리오

1. Claude CLI 경로를 잘못된 값으로 설정 (`CLAUDE_CODE_PATH=nonexistent`)
2. 백엔드 서버 재시작
3. `GET /api/v1/health/detailed` 호출
   - [ ] `claude_cli.status: "error"` 반환
4. 파이프라인 시작 시도
   - [ ] stage_error 이벤트 수신
   - [ ] 프론트엔드에 에러 메시지 표시

---

## 6. Tistory 발행 준비

### 사전 조건
- Playwright 설치 완료
- Tistory 블로그 URL 설정 (`TISTORY_BLOG_URL=https://jaylenhan.tistory.com`)

### 테스트 절차

1. 파이프라인 전체 완료 후 Publisher 단계 진행
2. 브라우저가 자동으로 열리는지 확인 (headless=False)
3. Tistory 로그인 페이지 → 수동 로그인
   - [ ] 로그인 완료 자동 감지
4. 에디터에 제목/본문이 자동 입력되는지 확인
   - [ ] 제목 필드에 글 제목
   - [ ] HTML 모드에서 본문 내용
5. 스크린샷이 `/tmp/tistory_preview.png`에 저장되는지 확인
6. **수동으로 "발행" 버튼 클릭** (자동 발행 절대 금지)

---

## 7. Health Check 상세

```bash
# 기본 health check
curl http://localhost:8000/api/v1/health

# 상세 health check (Claude CLI + mmdc + Obsidian vault)
curl http://localhost:8000/api/v1/health/detailed | jq
```

### 확인 항목
- [ ] `claude_cli.status: "ok"` + 버전 정보
- [ ] `mermaid_cli.status: "ok"` + 경로
- [ ] `obsidian_vault.status` — 설정에 따라 "ok" 또는 "disabled"

---

## 8. 동시 실행 방지

1. 파이프라인 실행 중 (Gate 대기 아닌 실제 진행 중)
2. 새 탭에서 같은 주제로 시작 시도
3. [ ] 정상적으로 별도 run이 생성됨 (충돌 없음)
4. [ ] 각 run의 이벤트가 독립적으로 처리됨
