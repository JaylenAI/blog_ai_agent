const SUBAGENTS = [
  {
    name: "Librarian Official",
    desc: "공식 문서 검색 (docs, specifications)",
    icon: "📚",
    status: "active",
  },
  {
    name: "Librarian GitHub",
    desc: "GitHub 저장소 및 코드 검색",
    icon: "🐙",
    status: "active",
  },
  {
    name: "Librarian Blog EN",
    desc: "영문 기술 블로그 검색",
    icon: "🌐",
    status: "active",
  },
  {
    name: "Librarian Blog KR",
    desc: "한국어 기술 블로그 검색",
    icon: "🇰🇷",
    status: "active",
  },
] as const;

export function SubagentsPanel() {
  return (
    <div className="sp-cards">
      <p className="sb-panel-note" style={{ marginBottom: 14 }}>
        Researcher 스테이지에서 4개 Librarian이 병렬로 자료를
        수집합니다.
      </p>
      {SUBAGENTS.map((a) => (
        <div key={a.name} className="sp-card">
          <div className="sp-card-head">
            <span className="sp-card-icon">{a.icon}</span>
            <span className="sp-card-name">{a.name}</span>
            <span className={`sp-status-badge ${a.status}`}>
              {a.status}
            </span>
          </div>
          <div className="sp-card-desc">{a.desc}</div>
        </div>
      ))}
    </div>
  );
}
