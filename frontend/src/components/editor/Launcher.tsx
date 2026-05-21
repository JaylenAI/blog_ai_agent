import { useState, useCallback } from "react";

interface LauncherProps {
  onStart: (topic: string, autoGateOne: boolean) => void;
  disabled: boolean;
}

export function Launcher({ onStart, disabled }: LauncherProps) {
  const [topic, setTopic] = useState("");
  const [autoGateOne, setAutoGateOne] = useState(false);

  const handleSubmit = useCallback(() => {
    const trimmed = topic.trim();
    if (!trimmed || disabled) return;
    onStart(trimmed, autoGateOne);
  }, [topic, autoGateOne, disabled, onStart]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8">
      <div className="max-w-xl w-full space-y-8 text-center">
        {/* Brand mark */}
        <span
          className="inline-flex items-center justify-center rounded-full text-white text-xl font-bold"
          style={{
            width: 48,
            height: 48,
            backgroundColor: "var(--color-accent)",
          }}
        >
          B
        </span>

        {/* Heading */}
        <div>
          <h1
            className="text-2xl font-semibold mb-2"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            오늘은 어떤 주제로 쓸까요?
          </h1>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            주제 한 줄을 입력하면 자료수집부터 발행 준비까지 30분 안에 완료됩니다.
            <br />
            Gate 1 · 2 검수는 절대 자동화하지 않습니다.
          </p>
        </div>

        {/* Input */}
        <div
          className="rounded-lg border p-4 text-left"
          style={{
            borderColor: "var(--color-border)",
            backgroundColor: "var(--color-bg-elev)",
          }}
        >
          <textarea
            className="w-full bg-transparent text-sm outline-none resize-none"
            rows={3}
            placeholder="예: 에이전틱 RAG에 대해 다이어그램 포함해서 깊게 정리해줘"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            style={{ color: "var(--color-text)" }}
          />

          <div className="flex items-center justify-between mt-3 pt-3 border-t" style={{ borderColor: "var(--color-border)" }}>
            <label
              className="flex items-center gap-2 text-xs cursor-pointer"
              style={{ color: "var(--color-text-muted)" }}
            >
              <input
                type="checkbox"
                checked={autoGateOne}
                onChange={(e) => setAutoGateOne(e.target.checked)}
                className="rounded"
              />
              Gate 1 자동 통과
            </label>

            <button
              className="text-sm px-4 py-1.5 rounded-md font-medium text-white transition-opacity disabled:opacity-40"
              style={{ backgroundColor: "var(--color-accent)" }}
              onClick={handleSubmit}
              disabled={disabled || !topic.trim()}
            >
              생성 시작 ⌘↵
            </button>
          </div>
        </div>

        {/* Cost note */}
        <p className="text-xs" style={{ color: "var(--color-text-faint)" }}>
          편당 추가 비용 $0 · Claude Code 구독으로만 운영
        </p>
      </div>
    </div>
  );
}
