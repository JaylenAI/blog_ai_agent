import { useCallback, useEffect } from "react";
import { usePipelineActions } from "../../hooks/use-pipeline-actions";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useAppStore } from "../../stores/app-store";
import { OutlinePreview } from "./OutlinePreview";
import { ContentPreview } from "./ContentPreview";

interface GateModalProps {
  gate: "gate_one" | "gate_two";
  runId: number;
  onClose: () => void;
}

const GATE_CONFIG = {
  gate_one: {
    title: "GATE 1 — 아웃라인 검수",
    approveLabel: "본문 생성 시작",
    description:
      "Stage 2~3이 완료되었습니다. 아웃라인을 확인하고 승인해 주세요.",
  },
  gate_two: {
    title: "GATE 2 — 최종 검수",
    approveLabel: "발행 준비 승인",
    description:
      "Validator 검증이 완료되었습니다. 최종 콘텐츠를 확인해 주세요.",
  },
};

export function GateModal({ gate, runId, onClose }: GateModalProps) {
  const { approveGate, rejectGate } = usePipelineActions();
  const isRunning = usePipelineStore((s) => s.isRunning);
  const config = GATE_CONFIG[gate];
  const closeGateModal = useAppStore((s) => s.closeGateModal);

  const handleApprove = useCallback(async () => {
    await approveGate(runId);
  }, [approveGate, runId]);

  const handleReject = useCallback(async () => {
    await rejectGate(runId);
  }, [rejectGate, runId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeGateModal();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [closeGateModal]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-xl shadow-xl"
        style={{ backgroundColor: "var(--color-bg-elev)" }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b shrink-0"
          style={{ borderColor: "var(--color-border)" }}
        >
          <div>
            <h2 className="text-base font-semibold">{config.title}</h2>
            <p
              className="text-xs mt-0.5"
              style={{ color: "var(--color-text-muted)" }}
            >
              {config.description}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-lg px-2"
            style={{ color: "var(--color-text-faint)" }}
            aria-label="닫기"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {gate === "gate_one" ? (
            <OutlinePreview />
          ) : (
            <ContentPreview runId={runId} />
          )}
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4 border-t shrink-0"
          style={{ borderColor: "var(--color-border)" }}
        >
          <button
            className="text-sm px-4 py-2 rounded-md transition-colors"
            style={{
              backgroundColor: "var(--color-bg-hover)",
              color: "var(--color-text-muted)",
            }}
            onClick={onClose}
            disabled={isRunning}
          >
            나중에
          </button>
          <button
            className="text-sm px-4 py-2 rounded-md transition-colors text-white disabled:opacity-40"
            style={{ backgroundColor: "var(--color-danger)" }}
            onClick={handleReject}
            disabled={isRunning}
          >
            거부
          </button>
          <button
            className="text-sm px-4 py-2 rounded-md transition-colors text-white disabled:opacity-40"
            style={{ backgroundColor: "var(--color-accent)" }}
            onClick={handleApprove}
            disabled={isRunning}
          >
            {isRunning ? "처리 중..." : config.approveLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
