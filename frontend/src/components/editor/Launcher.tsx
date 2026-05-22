import { useState, useCallback, useEffect, useRef } from "react";
import { Icons } from "../common/Icons";
import { api } from "../../api/client";
import type { BlogFormat, FormatSuggestion } from "../../types/format";

interface LauncherProps {
  onStart: (topic: string, autoGateOne: boolean, formatId: string) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  {
    cat: "AI/LLM",
    title: "에이전틱 RAG 완벽 가이드 2026",
    meta: "개념 해설 · 8~10K자 · 다이어그램 3장",
    format: "concept",
  },
  {
    cat: "DevOps",
    title: "MCP 서버 직접 구축하기",
    meta: "실습 튜토리얼 · Playwright 실습 포함",
    format: "tutorial",
  },
  {
    cat: "AI/LLM",
    title: "Claude Code vs Cursor 비교",
    meta: "비교 분석 · 비교표 3장 · 상황별 추천",
    format: "comparison",
  },
  {
    cat: "Backend",
    title: "한국어 LLM 파인튜닝 비용 분석",
    meta: "트렌드 분석 · 데이터 기반 · 전망",
    format: "trend",
  },
];

export function Launcher({ onStart, disabled }: LauncherProps) {
  const [topic, setTopic] = useState("");
  const [autoGate, setAutoGate] = useState(false);
  const [length, setLength] = useState<"standard" | "long">("standard");
  const [formats, setFormats] = useState<BlogFormat[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<string>("auto");
  const [suggestion, setSuggestion] = useState<FormatSuggestion | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    api.formats.list().then((res) => {
      if (res.data) setFormats(res.data);
    });
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const trimmed = topic.trim();
    if (trimmed.length < 3) {
      setSuggestion(null);
      return;
    }
    debounceRef.current = setTimeout(() => {
      api.formats.suggest(trimmed).then((res) => {
        if (res.data && res.data.length > 0) {
          setSuggestion(res.data[0] ?? null);
        } else {
          setSuggestion(null);
        }
      });
    }, 500);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [topic]);

  const resolvedFormat =
    selectedFormat === "auto"
      ? suggestion?.format_id ?? "concept"
      : selectedFormat;

  const handleSubmit = useCallback(
    (t?: string, fmt?: string) => {
      const text = (t ?? topic).trim();
      if (!text || disabled) return;
      onStart(text, autoGate, fmt ?? resolvedFormat);
    },
    [topic, autoGate, disabled, onStart, resolvedFormat],
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

  const activeFormat = formats.find((f) => f.id === resolvedFormat);

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

        <div className="format-bar">
          <button
            className={`fmt ${selectedFormat === "auto" ? "on" : ""}`}
            onClick={() => setSelectedFormat("auto")}
            title="주제에 따라 Router가 자동 결정"
          >
            <span className="fmt-icon">🔄</span> 자동
            {selectedFormat === "auto" && suggestion && (
              <span className="fmt-hint">→ {suggestion.icon} {suggestion.name}</span>
            )}
          </button>
          {formats.map((f) => (
            <button
              key={f.id}
              className={`fmt ${selectedFormat === f.id ? "on" : ""}`}
              onClick={() => setSelectedFormat(f.id)}
              title={f.description}
            >
              <span className="fmt-icon">{f.icon}</span>
              <span className="fmt-label">{f.name.replace("형", "")}</span>
            </button>
          ))}
        </div>

        {activeFormat && (
          <div className="format-desc">
            {activeFormat.icon} {activeFormat.description} ·{" "}
            {activeFormat.section_count_min}~{activeFormat.section_count_max}섹션 ·{" "}
            {(activeFormat.char_count_standard[0] / 1000).toFixed(0)}~
            {(activeFormat.char_count_standard[1] / 1000).toFixed(0)}K자
          </div>
        )}

        <div className="composer-foot">
          <button
            className={`opt ${length === "standard" ? "on" : ""}`}
            onClick={() => setLength("standard")}
            title="표준 분량"
          >
            <Icons.Doc s={11} /> 표준
          </button>
          <button
            className={`opt ${length === "long" ? "on" : ""}`}
            onClick={() => setLength("long")}
          >
            장문
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
            onClick={() => {
              setSelectedFormat(s.format);
              handleSubmit(s.title, s.format);
            }}
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
