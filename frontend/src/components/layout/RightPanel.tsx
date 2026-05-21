import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { Icons } from "../common/Icons";

interface PipelineStage {
  id: string;
  key: string;
  num: number | null;
  name: string;
  desc: string;
  expected: string;
  gate?: boolean;
}

const PIPELINE_STAGES: readonly PipelineStage[] = [
  { id: "router", key: "router", num: 1, name: "Router", desc: "주제 분석 · 키워드 추출 · 분량 결정", expected: "10~20초" },
  { id: "research", key: "researcher", num: 2, name: "Researcher", desc: "4-channel 자료수집 (병렬)", expected: "2~3분" },
  { id: "outline", key: "outliner", num: 3, name: "Outliner", desc: "7~9개 대섹션 + 출처 매핑", expected: "30~60초" },
  { id: "gate1", key: "gate_one", num: null, name: "Gate 1", desc: "사용자 아웃라인 승인", expected: "사람 검수", gate: true },
  { id: "generate", key: "generator", num: 4, name: "Generator", desc: "본문 + Mermaid/SVG 병렬 생성", expected: "3~5분" },
  { id: "validate", key: "validator", num: 5, name: "Validator", desc: "14항목 + SEO/AEO/GEO + oracle", expected: "30~60초" },
  { id: "gate2", key: "gate_two", num: null, name: "Gate 2", desc: "최종 승인 (필수, 자동화 불가)", expected: "사람 검수", gate: true },
  { id: "publish", key: "publisher", num: 6, name: "Publisher", desc: "md → Tistory HTML + 클립보드", expected: "1~2분" },
];

export function RightPanel() {
  const { rightPanelTab, setRightPanelTab, pipelineMode } = useAppStore();

  useEffect(() => {
    if (pipelineMode === "validate" || pipelineMode === "gate2") {
      setRightPanelTab("validation");
    } else if (pipelineMode === "research") {
      setRightPanelTab("pipeline");
    }
  }, [pipelineMode, setRightPanelTab]);

  return (
    <aside className="right-panel">
      <div className="rp-tabs">
        <button
          className={`rp-tab ${rightPanelTab === "pipeline" ? "active" : ""}`}
          onClick={() => setRightPanelTab("pipeline")}
        >
          <Icons.Layers s={13} /> 파이프라인
        </button>
        <button
          className={`rp-tab ${rightPanelTab === "references" ? "active" : ""}`}
          onClick={() => setRightPanelTab("references")}
        >
          <Icons.Tag s={13} /> 자료
        </button>
        <button
          className={`rp-tab ${rightPanelTab === "validation" ? "active" : ""}`}
          onClick={() => setRightPanelTab("validation")}
        >
          <Icons.CheckCircle s={13} /> 검증
        </button>
      </div>
      <div className="rp-body">
        {rightPanelTab === "pipeline" && <PipelineTab />}
        {rightPanelTab === "references" && <ReferencesTab />}
        {rightPanelTab === "validation" && <ValidationTab />}
      </div>
    </aside>
  );
}

function PipelineTab() {
  const events = usePipelineStore((s) => s.events);
  const { openGateModal, gateModal } = useAppStore();

  const completedStages = new Set(
    events.filter((e) => e.event_type === "stage_complete").map((e) => e.stage),
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

  const stageState = (key: string) => {
    if (completedStages.has(key)) return "done";
    if (activeStages.has(key)) return "active";
    if (pendingStages.has(key)) return "active";
    if (errorStages.has(key)) return "error";
    return "queued";
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        {PIPELINE_STAGES.map((p) => {
          const state = stageState(p.key);
          const cls = [
            "pl-stage",
            state,
            p.gate ? "gate" : "",
            state === "done" && p.gate ? "passed" : "",
          ]
            .filter(Boolean)
            .join(" ");

          const isPending = pendingStages.has(p.key);

          return (
            <div key={p.id} className={cls}>
              <span className="pl-icon">
                {state === "done" ? (
                  <Icons.Check s={11} w={2.5} />
                ) : p.gate ? (
                  <Icons.Lock s={10} w={2} />
                ) : (
                  <span style={{ fontSize: 10, fontWeight: 700 }}>
                    {p.num ?? "·"}
                  </span>
                )}
              </span>
              <div className="pl-title">
                {p.num && <span className="step">Stage {p.num}</span>}
                <span>{p.name}</span>
              </div>
              <div className="pl-meta">
                {p.desc} · {p.expected}
              </div>

              {isPending && p.gate && runId > 0 && (
                <div className="pl-detail" style={{ display: "block" }}>
                  <button
                    className="btn primary"
                    style={{ width: "100%", justifyContent: "center" }}
                    onClick={() =>
                      openGateModal(
                        p.key as "gate_one" | "gate_two",
                        runId,
                      )
                    }
                    disabled={gateModal !== null}
                  >
                    <Icons.Eye s={13} />{" "}
                    {p.key === "gate_one"
                      ? "아웃라인 검수 열기"
                      : "최종 검수 열기"}
                  </button>
                </div>
              )}

              {state === "active" && p.key === "researcher" && (
                <div className="pl-detail" style={{ display: "block" }}>
                  <LibrarianCards />
                  <EventLog />
                </div>
              )}

              {state === "active" && p.key === "generator" && (
                <div className="pl-detail" style={{ display: "block" }}>
                  <GenerateProgress />
                </div>
              )}

              {(state === "active" || state === "done") &&
                p.key === "validator" && (
                  <div
                    className="pl-detail"
                    style={{
                      display:
                        state === "active" ? "block" : undefined,
                    }}
                  >
                    <ValidateInline />
                  </div>
                )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LibrarianCards() {
  const events = usePipelineStore((s) => s.events);
  const librarians = [
    { id: "official", name: "librarian-official" },
    { id: "github", name: "librarian-github" },
    { id: "blog-en", name: "librarian-blog-en" },
    { id: "blog-kr", name: "librarian-blog-kr" },
  ] as const;

  return (
    <div className="lib-grid">
      {librarians.map((l) => {
        const completeEvent = events.find(
          (e) =>
            e.event_type === "stage_complete" &&
            e.stage === "researcher" &&
            e.data?.librarian === l.id,
        );
        const done = Boolean(completeEvent);
        const count =
          (completeEvent?.data?.reference_count as number | undefined) ?? 0;

        return (
          <div key={l.id} className={`lib-card ${done ? "done" : "busy"}`}>
            <div className="lib-name">{l.name}</div>
            <div className="lib-stat">
              {done ? `${count}건 · OK` : "수집 중…"}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function EventLog() {
  const events = usePipelineStore((s) => s.events);
  const recentEvents = events.slice(-7);

  if (recentEvents.length === 0) return null;

  return (
    <div className="log-stream">
      {recentEvents.map((e, i) => {
        const ts = e.data?.timestamp as string | undefined;
        const timeStr = ts ? formatTimestamp(ts) : "";

        return (
          <div key={i}>
            {timeStr && <span className="ts">{timeStr}</span>}
            <span className="tag">{e.stage.toUpperCase()}</span>
            <span className={e.event_type === "stage_complete" ? "ok" : ""}>
              {e.message}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
  } catch {
    return "";
  }
}

function GenerateProgress() {
  const events = usePipelineStore((s) => s.events);

  const outlineEvent = events.find(
    (e) => e.event_type === "gate_pending" && e.stage === "gate_one",
  );
  const totalSections =
    (outlineEvent?.data as { total_sections?: number } | undefined)
      ?.total_sections ??
    (outlineEvent?.data as { outline?: unknown[] } | undefined)?.outline
      ?.length ??
    0;

  const completedSections = events.filter(
    (e) =>
      e.event_type === "stage_complete" &&
      e.stage === "generator" &&
      (e.data as { section_number?: number } | undefined)?.section_number !=
        null,
  ).length;

  const completedImages = events.filter(
    (e) =>
      e.event_type === "stage_complete" &&
      e.stage === "generator" &&
      (e.data as { image?: boolean } | undefined)?.image === true,
  ).length;

  const totalImages =
    (
      events.find(
        (e) => e.event_type === "stage_start" && e.stage === "generator",
      )?.data as { total_images?: number } | undefined
    )?.total_images ?? 0;

  if (totalSections === 0 && totalImages === 0) return null;

  return (
    <div className="pl-meta" style={{ marginTop: 4 }}>
      {totalSections > 0 && (
        <span>
          섹션 {completedSections}/{totalSections} 작성 중
        </span>
      )}
      {totalImages > 0 && (
        <span>
          {" "}
          · 이미지 {completedImages}/{totalImages} 렌더 완료
        </span>
      )}
    </div>
  );
}

function ValidateInline() {
  const validationSummary = usePipelineStore((s) => s.validationSummary);
  if (!validationSummary) return null;

  return (
    <div className="validate-grid" style={{ marginTop: 6 }}>
      <div className="vstat pass">
        <div className="label">PASS</div>
        <div className="value" style={{ fontSize: 16 }}>
          {validationSummary.passed}
        </div>
      </div>
      <div className="vstat warn">
        <div className="label">WARN</div>
        <div className="value" style={{ fontSize: 16 }}>
          {validationSummary.failed}
        </div>
      </div>
      <div className="vstat">
        <div className="label">점수</div>
        <div className="value" style={{ fontSize: 16 }}>
          {Math.round(validationSummary.score * 100)}%
        </div>
      </div>
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
    return <div className="empty">파이프라인 실행 후 자료가 표시됩니다</div>;
  }

  const getRelevanceClass = (score: number) => {
    const r = Math.round(score * 5);
    if (r >= 5) return "r5";
    if (r >= 4) return "r4";
    return "r3";
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 10,
          fontSize: 12,
          color: "var(--text-muted)",
        }}
      >
        <span>
          총{" "}
          <strong style={{ color: "var(--text)" }}>{references.length}건</strong>{" "}
          확보 · 최소 기준 8건 충족
        </span>
      </div>
      {references.map((r, i) => (
        <div key={i} className="ref-row">
          <div className={`ref-rel ${getRelevanceClass(r.relevance_score)}`}>
            {Math.round(r.relevance_score * 5)}
          </div>
          <div className="ref-body">
            <div className="ref-title">{r.title}</div>
            <div className="ref-source">
              <span className="ref-type">{r.source_type}</span>
              <span>{safeHostname(r.url)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function safeHostname(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

function ValidationTab() {
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

  const CATEGORY_LABELS: Record<string, { title: string; pill: string }> = {
    style: { title: "STYLE.MD 양식", pill: `${grouped.get("style")?.length ?? 0}항목` },
    seo: { title: "SEO", pill: "검색엔진" },
    aeo: { title: "AEO", pill: "답변엔진" },
    geo: { title: "GEO", pill: "생성엔진" },
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
          <div className="value">{Math.round(validationSummary.score * 100)}%</div>
        </div>
      </div>

      {Array.from(grouped.entries()).map(([cat, items]) => {
        const labels = CATEGORY_LABELS[cat] ?? {
          title: cat.toUpperCase(),
          pill: "",
        };
        return (
          <div key={cat} className="vl-section">
            <div className="vl-section-title">
              {labels.title}{" "}
              {labels.pill && <span className="pill">{labels.pill}</span>}
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
