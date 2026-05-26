import { useCallback, useEffect, useState } from "react";
import { usePipelineActions } from "../../hooks/use-pipeline-actions";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useAppStore } from "../../stores/app-store";
import { OutlinePreview } from "./OutlinePreview";
import { ContentPreview } from "./ContentPreview";
import { Icons } from "../common/Icons";

interface GateModalProps {
  gate: "gate_one" | "gate_two";
  runId: number;
  onClose: () => void;
}

export function GateModal({ gate, runId, onClose }: GateModalProps) {
  const { approveGate, rejectGate, rejectAndRevise } = usePipelineActions();
  const isRunning = usePipelineStore((s) => s.isRunning);
  const closeGateModal = useAppStore((s) => s.closeGateModal);
  const [checklistComplete, setChecklistComplete] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);

  const isGate1 = gate === "gate_one";
  const approveDisabled = isRunning || (!isGate1 && !checklistComplete);

  const handleApprove = useCallback(async () => {
    await approveGate(runId);
  }, [approveGate, runId]);

  const handleReject = useCallback(async () => {
    if (isGate1 && feedback.trim()) {
      await rejectAndRevise(runId, feedback.trim());
    } else {
      await rejectGate(runId);
    }
  }, [isGate1, feedback, rejectGate, rejectAndRevise, runId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeGateModal();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [closeGateModal]);

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gate-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <span className="gate-badge">{isGate1 ? "GATE 1" : "GATE 2"}</span>
          <div className="modal-title" id="gate-modal-title">
            {isGate1 ? "아웃라인 검수" : "최종 검수 — Tistory 게시 전"}
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="닫기">
            <Icons.X />
          </button>
        </div>

        <div className="modal-body">
          {isGate1 ? (
            <Gate1Body />
          ) : (
            <Gate2Body runId={runId} onChecklistChange={setChecklistComplete} />
          )}
        </div>

        {isGate1 && showFeedback && (
          <div style={{ padding: "0 24px 12px" }}>
            <textarea
              className="gate-feedback-input"
              placeholder="예: 3번 섹션을 '기존 RAG와의 차이'로 바꿔줘"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={3}
              style={{
                width: "100%",
                resize: "vertical",
                background: "var(--bg-sub)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                padding: "10px 12px",
                fontSize: 13,
                color: "var(--text)",
                fontFamily: "inherit",
              }}
            />
          </div>
        )}

        <div className="modal-foot">
          <span className="filler">
            {isGate1
              ? showFeedback
                ? "피드백을 입력하면 아웃라인을 다시 생성합니다"
                : "Gate 1은 --auto 플래그로 건너뛸 수 있지만 기본은 사람이 검수"
              : checklistComplete
                ? "Gate 2는 절대 자동화 불가 — 사람만 결정"
                : "모든 체크리스트 항목을 확인해야 발행할 수 있습니다"}
          </span>
          {isGate1 && !showFeedback ? (
            <button
              className="btn ghost"
              onClick={() => setShowFeedback(true)}
              disabled={isRunning}
            >
              수정 요청
            </button>
          ) : (
            <button
              className="btn ghost"
              onClick={handleReject}
              disabled={isRunning}
            >
              {isGate1 && feedback.trim() ? "피드백 반영 재생성" : "수정 요청"}
            </button>
          )}
          <button
            className="btn subtle"
            onClick={onClose}
            disabled={isRunning}
          >
            나중에
          </button>
          <button
            className="btn primary"
            onClick={handleApprove}
            disabled={approveDisabled}
          >
            <Icons.Check s={13} w={2.5} />
            {isRunning
              ? "처리 중..."
              : isGate1
                ? "본문 생성 시작"
                : "Tistory에 발행 준비"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Gate1Body() {
  return (
    <>
      <div
        style={{
          fontSize: 13,
          color: "var(--text-muted)",
          marginBottom: 16,
          lineHeight: 1.55,
        }}
      >
        Stage 2~3이 완료되었습니다. 아웃라인을 확인하고 승인해 주세요.
        <br />
        진행하기 전에 구조와 출처 매핑을 확인해 주세요.
      </div>
      <OutlinePreview />
      <div
        style={{
          marginTop: 16,
          padding: 12,
          background: "var(--bg-sub)",
          borderRadius: 8,
          fontSize: 12,
          color: "var(--text-muted)",
        }}
      >
        <strong style={{ color: "var(--text)" }}>💡 수정 예시:</strong>{" "}
        &ldquo;3번 섹션을 &lsquo;기존 RAG와의 차이&rsquo;로 바꿔줘&rdquo;
        처럼 자연어로 요청하면 아웃라인을 다시 짭니다.
      </div>
    </>
  );
}

function Gate2Body({
  runId,
  onChecklistChange,
}: {
  runId: number;
  onChecklistChange: (allChecked: boolean) => void;
}) {
  const validationSummary = usePipelineStore((s) => s.validationSummary);

  return (
    <>
      <div
        style={{
          fontSize: 13,
          color: "var(--text-muted)",
          marginBottom: 16,
          lineHeight: 1.55,
        }}
      >
        {validationSummary && (
          <>
            Validator{" "}
            <strong style={{ color: "var(--text)" }}>
              {validationSummary.passed}/
              {validationSummary.passed + validationSummary.failed} 통과
            </strong>
            .{" "}
          </>
        )}
        이 게이트는{" "}
        <strong style={{ color: "var(--text)" }}>
          절대 자동화하지 않습니다.
        </strong>{" "}
        실제로 발행할지 사람이 결정합니다.
      </div>

      {validationSummary && (
        <div className="validate-grid" style={{ marginBottom: 16 }}>
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
      )}

      <HighlightSection />
      <ContentPreview runId={runId} />
      <PrePublishChecklist runId={runId} onAllChecked={onChecklistChange} />
    </>
  );
}

function HighlightSection() {
  const validations = usePipelineStore((s) => s.validations);
  const passedItems = validations.filter((v) => v.passed).slice(0, 5);

  if (passedItems.length === 0) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <div className="vl-section-title">
        하이라이트 — 통과 항목 일부
        <span className="pill">{passedItems.length}건 표시</span>
      </div>
      {passedItems.map((v, i) => (
        <div key={i} className="vl-row pass">
          <span className="vl-ico">
            <Icons.Check s={9} w={2.5} />
          </span>
          <span className="vl-name">{v.item}</span>
          <span className="vl-num">{Math.round(v.score * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

const CHECKLIST_ITEMS = [
  "카테고리 태그 10개 확인",
  "JSON-LD TechArticle + HowTo schema 삽입",
  "이미지 alt 태그 부여",
  "마치며 3단 서사 구조 확인",
  "OG:image 메타 확인",
  "내부 링크 2개 이상 삽입",
] as const;

function PrePublishChecklist({ runId, onAllChecked }: { runId: number; onAllChecked: (allChecked: boolean) => void }) {
  const storageKey = `gate2-checklist-${runId}`;

  const [checked, setChecked] = useState<Record<number, boolean>>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved) as Record<string, boolean>;
        const restored: Record<number, boolean> = {};
        for (const [k, v] of Object.entries(parsed)) restored[Number(k)] = v;
        const count = Object.values(restored).filter(Boolean).length;
        if (count === CHECKLIST_ITEMS.length) onAllChecked(true);
        return restored;
      }
    } catch { /* ignore parse errors */ }
    return {};
  });

  const toggle = (index: number) => {
    setChecked((prev) => {
      const next = { ...prev, [index]: !prev[index] };
      const count = Object.values(next).filter(Boolean).length;
      onAllChecked(count === CHECKLIST_ITEMS.length);
      try { localStorage.setItem(storageKey, JSON.stringify(next)); } catch { /* quota */ }
      return next;
    });
  };

  const checkedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div
      style={{
        marginTop: 16,
        padding: 14,
        background: "var(--bg-sub)",
        borderRadius: "var(--radius)",
        fontSize: 12,
        lineHeight: 1.7,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 8,
          fontWeight: 600,
          fontSize: 13,
          color: "var(--text)",
        }}
      >
        <span>📌 발행 직전 체크</span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 11,
            color: "var(--text-muted)",
          }}
        >
          {checkedCount}/{CHECKLIST_ITEMS.length}
        </span>
      </div>
      {CHECKLIST_ITEMS.map((item, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "3px 0",
            cursor: "pointer",
            color: checked[i] ? "var(--text-faint)" : "var(--text-muted)",
            textDecoration: checked[i] ? "line-through" : "none",
          }}
          onClick={() => toggle(i)}
          onKeyDown={(e) => { if (e.key === " " || e.key === "Enter") toggle(i); }}
          role="checkbox"
          aria-checked={checked[i]}
          tabIndex={0}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: "var(--radius-xs)",
              border: `1.5px solid ${checked[i] ? "var(--success)" : "var(--border-strong)"}`,
              background: checked[i] ? "var(--success)" : "transparent",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
              color: "white",
              fontSize: 9,
            }}
          >
            {checked[i] && <Icons.Check s={9} w={2.5} />}
          </span>
          <span>{item}</span>
        </div>
      ))}
    </div>
  );
}
