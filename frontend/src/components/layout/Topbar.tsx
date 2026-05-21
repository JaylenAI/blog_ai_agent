import { useAppStore } from "../../stores/app-store";

const MODE_LABELS: Record<string, string> = {
  idle: "",
  research: "Researcher · 자료수집 중",
  outline: "Gate 1 · 아웃라인 대기",
  generate: "Generator · 본문 생성 중",
  validate: "Validator · 검증 중",
  gate2: "Gate 2 · 최종 검수",
  published: "발행 완료",
};

export function Topbar() {
  const {
    sidebarOpen,
    toggleSidebar,
    activeArticle,
    pipelineMode,
    toggleRightPanel,
  } = useAppStore();

  const label = MODE_LABELS[pipelineMode] ?? "";
  const isLive = pipelineMode !== "idle" && pipelineMode !== "published";
  const isDone = pipelineMode === "published";

  return (
    <header
      className="flex items-center gap-3 px-4 border-b shrink-0"
      style={{
        height: "var(--top-h)",
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-bg-elev)",
      }}
    >
      {/* Sidebar toggle */}
      <button
        onClick={toggleSidebar}
        className="text-sm"
        style={{ color: "var(--color-text-muted)" }}
        aria-label={sidebarOpen ? "사이드바 닫기" : "사이드바 열기"}
      >
        &#9776;
      </button>

      {/* Breadcrumb */}
      <div
        className="flex-1 text-sm truncate"
        style={{ color: "var(--color-text-muted)" }}
      >
        {activeArticle
          ? `AI의 정석 / Drafts / ${activeArticle.title ?? activeArticle.topic}`
          : "AI의 정석"}
      </div>

      {/* Pipeline pill */}
      {label && (
        <span
          className="text-xs px-2.5 py-1 rounded-full font-medium"
          style={{
            backgroundColor: isDone
              ? "color-mix(in oklch, var(--color-success) 15%, transparent)"
              : isLive
                ? "color-mix(in oklch, var(--color-accent) 15%, transparent)"
                : "var(--color-bg-sub)",
            color: isDone
              ? "var(--color-success)"
              : isLive
                ? "var(--color-accent)"
                : "var(--color-text-muted)",
          }}
        >
          {isLive && (
            <span
              className="inline-block w-1.5 h-1.5 rounded-full mr-1.5 animate-pulse"
              style={{
                backgroundColor: "var(--color-accent)",
              }}
            />
          )}
          {label}
        </span>
      )}

      {/* Right panel toggle */}
      <button
        onClick={toggleRightPanel}
        className="text-xs px-2 py-1 rounded transition-colors"
        style={{
          backgroundColor: "var(--color-bg-hover)",
          color: "var(--color-text-muted)",
        }}
      >
        파이프라인
      </button>
    </header>
  );
}
