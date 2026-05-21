import { useState, useCallback } from "react";
import { Icons } from "../common/Icons";

interface LauncherProps {
  onStart: (topic: string, autoGateOne: boolean) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  {
    cat: "AI/LLM",
    title: "에이전틱 RAG 완벽 가이드 2026",
    meta: "표준 분량 · 8~10K자 · 다이어그램 3장",
  },
  {
    cat: "DevOps",
    title: "MCP 서버 직접 구축하기",
    meta: "장문 · Stage 6 Playwright 실습 포함",
  },
  {
    cat: "AI/LLM",
    title: "Claude Agent SDK 입문",
    meta: "표준 분량 · 비교 분석 중심",
  },
  {
    cat: "Backend",
    title: "한국어 LLM 파인튜닝 비용 분석",
    meta: "정량 비교 · matplotlib 차트",
  },
];

export function Launcher({ onStart, disabled }: LauncherProps) {
  const [topic, setTopic] = useState("");
  const [autoGate, setAutoGate] = useState(false);
  const [length, setLength] = useState<"standard" | "long">("standard");

  const handleSubmit = useCallback(
    (t?: string) => {
      const text = (t ?? topic).trim();
      if (!text || disabled) return;
      onStart(text, autoGate);
    },
    [topic, autoGate, disabled, onStart],
  );

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
    <div className="launcher">
      <div className="launcher-mark">B</div>
      <h1>오늘은 어떤 주제로 쓸까요?</h1>
      <div className="sub">
        주제 한 줄을 입력하면 자료수집부터 발행 준비까지 30분 안에 완료됩니다.
        <br />
        Gate 1·2 검수는 절대 자동화하지 않습니다.
      </div>

      <div className="composer">
        <div className="composer-prompt">
          <Icons.Sparkle s={13} /> /blog
        </div>
        <textarea
          className="composer-input"
          rows={2}
          placeholder="예: 에이전틱 RAG에 대해 다이어그램 포함해서 깊게 정리해줘"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <div className="composer-foot">
          <button
            className={`opt ${length === "standard" ? "on" : ""}`}
            onClick={() => setLength("standard")}
            title="대섹션 7~9개"
          >
            <Icons.Doc s={11} /> 표준 7~9 섹션
          </button>
          <button
            className={`opt ${length === "long" ? "on" : ""}`}
            onClick={() => setLength("long")}
          >
            장문 9~11
          </button>
          <button className="opt" title="자료 직접 첨부">
            <Icons.Plus s={11} /> 참고 자료
          </button>
          <button
            className={`opt ${autoGate ? "on" : ""}`}
            onClick={() => setAutoGate((v) => !v)}
            title="--auto 플래그: Gate 1만 건너뜀. Gate 2는 절대 불가"
          >
            <Icons.Lock s={11} /> Gate 1 자동
          </button>
          <button
            className="go"
            onClick={() => handleSubmit()}
            disabled={disabled || !topic.trim()}
          >
            <Icons.Sparkle s={12} /> 생성 시작
            <span className="kbd">⌘ ↵</span>
          </button>
        </div>
      </div>

      <div className="launcher-tip">
        <Icons.CheckCircle s={12} /> 편당 추가 비용 $0 · Claude Code 구독으로만
        운영
      </div>

      <div className="suggestion-grid">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            className="sug"
            onClick={() => handleSubmit(s.title)}
            disabled={disabled}
          >
            <div className="sug-cat">{s.cat}</div>
            <div className="sug-title">{s.title}</div>
            <div className="sug-meta">{s.meta}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
