import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";

const TABS = [
  { key: "pipeline" as const, label: "파이프라인" },
  { key: "references" as const, label: "자료" },
  { key: "validation" as const, label: "검증" },
];

const STAGES = [
  { key: "router", label: "Router", desc: "주제 분석 · 키워드 추출" },
  { key: "researcher", label: "Researcher", desc: "4-channel 자료수집" },
  { key: "outliner", label: "Outliner", desc: "7~9개 대섹션 아웃라인" },
  { key: "gate_one", label: "Gate 1", desc: "아웃라인 검수" },
  { key: "generator", label: "Generator", desc: "본문 + 다이어그램 생성" },
  { key: "validator", label: "Validator", desc: "양식 검증" },
  { key: "gate_two", label: "Gate 2", desc: "최종 검수 (자동화 불가)" },
  { key: "publisher", label: "Publisher", desc: "Obsidian · Tistory 발행" },
];

const CATEGORY_LABELS: Record<string, string> = {
  style: "STYLE",
  seo: "SEO",
  aeo: "AEO",
  geo: "GEO",
};

export function RightPanel() {
  const { rightPanelTab, setRightPanelTab } = useAppStore();

  return (
    <aside
      className="flex flex-col border-l h-full overflow-y-auto"
      style={{
        width: "var(--right-w)",
        minWidth: "var(--right-w)",
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-bg-elev)",
      }}
    >
      {/* Tabs */}
      <div
        className="flex border-b shrink-0"
        style={{ borderColor: "var(--color-border)" }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className="flex-1 text-xs py-2.5 font-medium transition-colors"
            style={{
              color:
                rightPanelTab === tab.key
                  ? "var(--color-accent)"
                  : "var(--color-text-muted)",
              borderBottom:
                rightPanelTab === tab.key
                  ? "2px solid var(--color-accent)"
                  : "2px solid transparent",
            }}
            onClick={() => setRightPanelTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 p-4">
        {rightPanelTab === "pipeline" && <PipelineTab />}
        {rightPanelTab === "references" && <ReferencesTab />}
        {rightPanelTab === "validation" && <ValidationTab />}
      </div>
    </aside>
  );
}

function PipelineTab() {
  const events = usePipelineStore((s) => s.events);
  const { gateModal, openGateModal } = useAppStore();

  const completedStages = new Set(
    events
      .filter((e) => e.event_type === "stage_complete")
      .map((e) => e.stage),
  );
  const errorStages = new Set(
    events.filter((e) => e.event_type === "stage_error").map((e) => e.stage),
  );
  const pendingStages = new Set(
    events.filter((e) => e.event_type === "gate_pending").map((e) => e.stage),
  );
  const activeStages = new Set(
    events
      .filter(
        (e) =>
          e.event_type === "stage_start" &&
          !completedStages.has(e.stage) &&
          !errorStages.has(e.stage) &&
          !pendingStages.has(e.stage),
      )
      .map((e) => e.stage),
  );

  const runId =
    (events.find((e) => e.data?.run_id != null)?.data?.run_id as number) ?? 0;

  return (
    <div className="space-y-1">
      {STAGES.map((stage) => {
        const done = completedStages.has(stage.key);
        const error = errorStages.has(stage.key);
        const pending = pendingStages.has(stage.key);
        const active = activeStages.has(stage.key);

        let icon: string;
        let iconColor: string;
        if (error) {
          icon = "!";
          iconColor = "var(--color-danger)";
        } else if (done) {
          icon = "✓";
          iconColor = "var(--color-success)";
        } else if (pending) {
          icon = "●";
          iconColor = "var(--color-warn)";
        } else if (active) {
          icon = "◉";
          iconColor = "var(--color-accent)";
        } else {
          icon = "○";
          iconColor = "var(--color-text-faint)";
        }

        const isGate =
          stage.key === "gate_one" || stage.key === "gate_two";

        return (
          <div key={stage.key} className="flex items-start gap-2 py-1.5">
            <span
              className={`text-xs font-bold mt-0.5 ${active ? "animate-pulse" : ""}`}
              style={{ color: iconColor, minWidth: 14, textAlign: "center" }}
            >
              {icon}
            </span>
            <div className="flex-1">
              <div className="text-sm font-medium">{stage.label}</div>
              <div
                className="text-xs"
                style={{ color: "var(--color-text-faint)" }}
              >
                {stage.desc}
              </div>
            </div>
            {pending && isGate && runId > 0 && (
              <button
                className="text-xs px-2 py-0.5 rounded"
                style={{
                  backgroundColor: "var(--color-bg-hover)",
                  color: "var(--color-accent)",
                }}
                onClick={() =>
                  openGateModal(
                    stage.key as "gate_one" | "gate_two",
                    runId,
                  )
                }
                disabled={gateModal !== null}
              >
                열기
              </button>
            )}
          </div>
        );
      })}

      {/* Event log */}
      {events.length > 0 && (
        <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--color-border)" }}>
          <div
            className="text-xs font-medium mb-2"
            style={{ color: "var(--color-text-faint)" }}
          >
            이벤트 로그
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {events.map((e, i) => (
              <div
                key={i}
                className="text-xs flex gap-2"
                style={{ color: "var(--color-text-muted)" }}
              >
                <span
                  className="shrink-0 uppercase"
                  style={{
                    color:
                      e.event_type === "stage_error"
                        ? "var(--color-danger)"
                        : e.event_type === "stage_complete"
                          ? "var(--color-success)"
                          : "var(--color-text-faint)",
                    minWidth: 56,
                  }}
                >
                  {e.stage}
                </span>
                <span className="truncate">{e.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ReferencesTab() {
  const events = usePipelineStore((s) => s.events);

  const researchEvent = events.find(
    (e) => e.event_type === "stage_complete" && e.stage === "researcher",
  );
  const references = (researchEvent?.data?.references ?? []) as Array<{
    url: string;
    title: string;
    summary: string;
    relevance_score: number;
    source_type: string;
  }>;

  if (references.length === 0) {
    return (
      <div
        className="text-sm text-center py-8"
        style={{ color: "var(--color-text-faint)" }}
      >
        파이프라인 실행 후 자료가 표시됩니다
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-xs" style={{ color: "var(--color-text-faint)" }}>
        총 {references.length}건 확보
      </div>
      {references.map((ref, i) => (
        <div
          key={i}
          className="p-2.5 rounded-md"
          style={{ backgroundColor: "var(--color-bg-sub)" }}
        >
          <div className="flex items-start gap-2">
            <span
              className="text-xs font-bold shrink-0 px-1.5 py-0.5 rounded"
              style={{
                backgroundColor:
                  ref.relevance_score >= 0.8
                    ? "color-mix(in oklch, var(--color-success) 20%, transparent)"
                    : "var(--color-bg-hover)",
                color:
                  ref.relevance_score >= 0.8
                    ? "var(--color-success)"
                    : "var(--color-text-faint)",
              }}
            >
              {Math.round(ref.relevance_score * 5)}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{ref.title}</div>
              <div
                className="text-xs mt-0.5 truncate"
                style={{ color: "var(--color-text-faint)" }}
              >
                {ref.source_type} · {new URL(ref.url).hostname}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ValidationTab() {
  const { validations, validationSummary } = usePipelineStore();

  if (!validationSummary) {
    return (
      <div
        className="text-sm text-center py-8"
        style={{ color: "var(--color-text-faint)" }}
      >
        검증 결과 없음
      </div>
    );
  }

  const grouped = new Map<string, typeof validations>();
  for (const v of validations) {
    const cat = v.category;
    const list = grouped.get(cat) ?? [];
    list.push(v);
    grouped.set(cat, list);
  }

  return (
    <div className="space-y-4">
      {/* Summary pills */}
      <div className="flex gap-2">
        <SummaryPill
          label="PASS"
          count={validationSummary.passed}
          color="var(--color-success)"
        />
        <SummaryPill
          label="FAIL"
          count={validationSummary.failed}
          color="var(--color-danger)"
        />
        <SummaryPill
          label="점수"
          count={Math.round(validationSummary.score * 100)}
          color="var(--color-accent)"
          suffix="%"
        />
      </div>

      {/* Grouped by category */}
      {Array.from(grouped.entries()).map(([cat, items]) => {
        const passed = items.filter((v) => v.passed).length;
        const pct = Math.round((passed / items.length) * 100);

        return (
          <div key={cat}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold">
                {CATEGORY_LABELS[cat] ?? cat.toUpperCase()}
              </span>
              <div
                className="flex-1 h-1.5 rounded-full overflow-hidden"
                style={{ backgroundColor: "var(--color-bg-sub)" }}
              >
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${pct}%`,
                    backgroundColor:
                      pct === 100
                        ? "var(--color-success)"
                        : "var(--color-warn)",
                  }}
                />
              </div>
              <span
                className="text-xs"
                style={{ color: "var(--color-text-faint)" }}
              >
                {passed}/{items.length}
              </span>
            </div>

            <div className="space-y-0.5">
              {items.map((v, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-sm py-1 px-2 rounded"
                  style={{
                    backgroundColor: v.passed
                      ? "transparent"
                      : "color-mix(in oklch, var(--color-danger) 5%, transparent)",
                  }}
                >
                  <span
                    style={{
                      color: v.passed
                        ? "var(--color-success)"
                        : "var(--color-danger)",
                    }}
                  >
                    {v.passed ? "✓" : "✗"}
                  </span>
                  <span className="flex-1 truncate">{v.item}</span>
                  <span
                    className="text-xs"
                    style={{ color: "var(--color-text-faint)" }}
                  >
                    {Math.round(v.score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SummaryPill({
  label,
  count,
  color,
  suffix = "",
}: {
  label: string;
  count: number;
  color: string;
  suffix?: string;
}) {
  return (
    <div
      className="flex-1 text-center py-2 rounded-md"
      style={{ backgroundColor: "var(--color-bg-sub)" }}
    >
      <div className="text-lg font-semibold" style={{ color }}>
        {count}
        {suffix}
      </div>
      <div
        className="text-xs font-medium"
        style={{ color: "var(--color-text-faint)" }}
      >
        {label}
      </div>
    </div>
  );
}
