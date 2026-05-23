import { usePipelineStore } from "../../stores/pipeline-store";
import { Icons } from "../common/Icons";

const CATEGORY_LABELS: Record<
  string,
  { title: string; pill: string }
> = {
  style: { title: "STYLE.MD 양식", pill: "" },
  seo: { title: "SEO", pill: "검색엔진" },
  aeo: { title: "AEO", pill: "답변엔진" },
  geo: { title: "GEO", pill: "생성엔진" },
};

export function ValidationTab() {
  const { validations, validationSummary } = usePipelineStore();

  if (!validationSummary) {
    return <div className="empty">검증 결과 없음</div>;
  }

  const grouped = new Map<string, typeof validations>();
  for (const v of validations) {
    const list = grouped.get(v.category) ?? [];
    list.push(v);
    grouped.set(v.category, list);
  }

  const categoryLabels = {
    ...CATEGORY_LABELS,
    style: {
      title: "STYLE.MD 양식",
      pill: `${grouped.get("style")?.length ?? 0}항목`,
    },
  };

  return (
    <div>
      <div className="validate-grid">
        <div className="vstat pass">
          <div className="label">PASS</div>
          <div className="value">{validationSummary.passed}</div>
        </div>
        <div className="vstat warn">
          <div className="label">WARN</div>
          <div className="value">{validationSummary.failed}</div>
        </div>
        <div className="vstat">
          <div className="label">점수</div>
          <div className="value">
            {Math.round(validationSummary.score * 100)}%
          </div>
        </div>
      </div>

      {Array.from(grouped.entries()).map(([cat, items]) => {
        const labels = categoryLabels[
          cat as keyof typeof categoryLabels
        ] ?? {
          title: cat.toUpperCase(),
          pill: "",
        };
        return (
          <div key={cat} className="vl-section">
            <div className="vl-section-title">
              {labels.title}{" "}
              {labels.pill && (
                <span className="pill">{labels.pill}</span>
              )}
            </div>
            {items.map((v, i) => (
              <div
                key={i}
                className={`vl-row ${v.passed ? "pass" : "warn"}`}
              >
                <span className="vl-ico">
                  {v.passed ? (
                    <Icons.Check s={9} w={2.5} />
                  ) : (
                    "!"
                  )}
                </span>
                <span className="vl-name">{v.item}</span>
                <span className="vl-num">
                  {Math.round(v.score * 100)}%
                </span>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
