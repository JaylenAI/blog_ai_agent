const SKILLS = [
  {
    name: "Router",
    desc: "주제 분석, 카테고리 결정, SEO 키워드 계획",
    stage: 1,
  },
  {
    name: "Researcher",
    desc: "4채널 병렬 자료조사 (WebSearch/WebFetch)",
    stage: 2,
  },
  {
    name: "Outliner",
    desc: "아웃라인 생성 + Gate 1 검수",
    stage: 3,
  },
  {
    name: "Generator",
    desc: "본문 작성 + 다이어그램/썸네일 생성",
    stage: 4,
  },
  {
    name: "Validator",
    desc: "14+8항목 양식 검증 + Gate 2 검수",
    stage: 5,
  },
  {
    name: "Publisher",
    desc: "Tistory Playwright 배포",
    stage: 6,
  },
] as const;

export function SkillsPanel() {
  return (
    <div className="sp-skills">
      <p className="sb-panel-note" style={{ marginBottom: 14 }}>
        6 Stage 파이프라인 각 단계별 스킬 목록입니다.
      </p>
      {SKILLS.map((sk) => (
        <div key={sk.stage} className="sp-skill-row">
          <div className="sp-skill-num">{sk.stage}</div>
          <div className="sp-skill-body">
            <div className="sp-skill-name">{sk.name}</div>
            <div className="sp-skill-desc">{sk.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
