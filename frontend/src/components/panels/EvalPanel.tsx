const EVAL_CATEGORIES = [
  { name: "Style", desc: "톤, 격식체, 구조 검증", items: 14 },
  { name: "SEO", desc: "검색엔진 최적화 체크", items: 4 },
  { name: "AEO", desc: "AI 엔진 최적화 체크", items: 2 },
  { name: "GEO", desc: "생성형 AI 최적화 체크", items: 2 },
] as const;

export function EvalPanel() {
  const totalItems = EVAL_CATEGORIES.reduce(
    (sum, c) => sum + c.items,
    0,
  );

  return (
    <div className="sp-eval">
      <p className="sb-panel-note" style={{ marginBottom: 14 }}>
        Validator 스테이지에서 총 {totalItems}개 항목을 자동 검증합니다.
        Gate 2에서 사람이 최종 확인합니다.
      </p>
      <div className="sp-eval-grid">
        {EVAL_CATEGORIES.map((cat) => (
          <div key={cat.name} className="sp-eval-card">
            <div className="sp-eval-card-head">
              <span className="sp-eval-card-name">{cat.name}</span>
              <span className="sp-eval-card-count">{cat.items}항목</span>
            </div>
            <div className="sp-card-desc">{cat.desc}</div>
          </div>
        ))}
      </div>
      <div className="sp-eval-total">
        <span>전체 검증 항목</span>
        <span className="sp-eval-total-num">{totalItems}</span>
      </div>
    </div>
  );
}
