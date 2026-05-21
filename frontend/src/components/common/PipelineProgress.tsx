import { usePipelineStore } from "../../stores/pipeline-store";

const STAGES = [
  { key: "router", label: "주제 분석" },
  { key: "researcher", label: "자료 수집" },
  { key: "outliner", label: "아웃라인" },
  { key: "gate_one", label: "Gate 1" },
  { key: "generator", label: "본문 작성" },
  { key: "validator", label: "검증" },
  { key: "gate_two", label: "Gate 2" },
  { key: "publisher", label: "발행" },
];

export function PipelineProgress() {
  const events = usePipelineStore((s) => s.events);
  const isRunning = usePipelineStore((s) => s.isRunning);

  if (events.length === 0 && !isRunning) return null;

  const completedStages = new Set(
    events
      .filter((e) => e.event_type === "stage_complete")
      .map((e) => e.stage),
  );

  const currentStage = events
    .filter((e) => e.event_type === "stage_start")
    .map((e) => e.stage)
    .pop();

  const errorStage = events
    .filter((e) => e.event_type === "stage_error")
    .map((e) => e.stage)
    .pop();

  const gateStage = events
    .filter((e) => e.event_type === "gate_pending")
    .map((e) => e.stage)
    .pop();

  return (
    <div
      className="flex items-center gap-1 px-4 py-2 text-xs border-b"
      style={{ borderColor: "var(--color-border)" }}
    >
      {STAGES.map(({ key, label }) => {
        let status: "idle" | "active" | "done" | "error" | "gate" = "idle";
        if (completedStages.has(key)) status = "done";
        if (key === currentStage && isRunning) status = "active";
        if (key === errorStage) status = "error";
        if (key === gateStage) status = "gate";

        return (
          <div key={key} className="flex items-center gap-1">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{
                backgroundColor:
                  status === "done"
                    ? "var(--color-success, #22c55e)"
                    : status === "active"
                      ? "var(--color-accent)"
                      : status === "error"
                        ? "var(--color-danger, #ef4444)"
                        : status === "gate"
                          ? "var(--color-warning, #f59e0b)"
                          : "var(--color-text-faint)",
                animation: status === "active" ? "pulse 1.5s infinite" : "none",
              }}
            />
            <span
              style={{
                color:
                  status === "idle"
                    ? "var(--color-text-faint)"
                    : "var(--color-text-muted)",
                fontWeight: status === "active" ? 600 : 400,
              }}
            >
              {label}
            </span>
            {key !== "publisher" && (
              <span
                className="mx-1"
                style={{ color: "var(--color-text-faint)" }}
              >
                →
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
