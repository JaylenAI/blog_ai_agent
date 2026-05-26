import { usePipelineStore } from "../../stores/pipeline-store";
import { useAppStore } from "../../stores/app-store";
import { Icons } from "../common/Icons";
import { PIPELINE_STAGES } from "./pipeline-stages";

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    const h = String(d.getHours()).padStart(2, "0");
    const m = String(d.getMinutes()).padStart(2, "0");
    const s = String(d.getSeconds()).padStart(2, "0");
    return `${h}:${m}:${s}`;
  } catch {
    return "";
  }
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
          (completeEvent?.data?.reference_count as number | undefined) ??
          0;

        return (
          <div
            key={l.id}
            className={`lib-card ${done ? "done" : "busy"}`}
          >
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
            <span
              className={
                e.event_type === "stage_complete" ? "ok" : ""
              }
            >
              {e.message}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function GenerateProgress() {
  const progress = usePipelineStore((s) => s.sectionProgress);

  if (!progress || progress.totalSections === 0) return null;

  const pct = Math.round(
    (progress.completedSections / progress.totalSections) * 100,
  );

  return (
    <div style={{ marginTop: 4 }}>
      <div className="pl-meta">
        {progress.status === "writing" ? (
          <span>
            섹션 {progress.currentSection}/{progress.totalSections} 작성 중
            {progress.currentHeading && ` · ${progress.currentHeading}`}
          </span>
        ) : (
          <span>
            섹션 {progress.completedSections}/{progress.totalSections} 완료
            {progress.currentHeading && ` · ${progress.currentHeading}`}
          </span>
        )}
      </div>
      <div
        style={{
          marginTop: 4,
          height: 4,
          borderRadius: 2,
          background: "var(--bg-tertiary, #2a2a2a)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            borderRadius: 2,
            background: "var(--accent, #60a5fa)",
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}

function ValidateInline() {
  const validationSummary = usePipelineStore(
    (s) => s.validationSummary,
  );
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

export function PipelineTab() {
  const events = usePipelineStore((s) => s.events);
  const { openGateModal, gateModal } = useAppStore();

  const completedStages = new Set(
    events
      .filter((e) => e.event_type === "stage_complete")
      .map((e) => e.stage),
  );
  const errorStages = new Set(
    events
      .filter((e) => e.event_type === "stage_error")
      .map((e) => e.stage),
  );
  const pendingStages = new Set(
    events
      .filter((e) => e.event_type === "gate_pending")
      .map((e) => e.stage),
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
    (events.find((e) => e.data?.run_id != null)?.data
      ?.run_id as number) ?? 0;

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
                {p.num && (
                  <span className="step">Stage {p.num}</span>
                )}
                <span>{p.name}</span>
              </div>
              <div className="pl-meta">
                {p.desc} · {p.expected}
              </div>

              {isPending && p.gate && runId > 0 && (
                <div
                  className="pl-detail"
                  style={{ display: "block" }}
                >
                  <button
                    className="btn primary"
                    style={{
                      width: "100%",
                      justifyContent: "center",
                    }}
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
                <div
                  className="pl-detail"
                  style={{ display: "block" }}
                >
                  <LibrarianCards />
                  <EventLog />
                </div>
              )}

              {state === "active" && p.key === "generator" && (
                <div
                  className="pl-detail"
                  style={{ display: "block" }}
                >
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
