import { useAppStore } from "../../stores/app-store";
import { Icons } from "../common/Icons";

const STAGE_LABELS: Record<
  string,
  { txt: string; cls: string }
> = {
  idle: { txt: "준비", cls: "" },
  research: { txt: "Researcher · 자료수집 중", cls: "live" },
  outline: { txt: "Gate 1 · 아웃라인 대기", cls: "live" },
  generate: { txt: "Generator · 본문 생성 중", cls: "live" },
  validate: { txt: "Validator · 14항목 검증", cls: "live" },
  gate2: { txt: "Gate 2 · 최종 검수", cls: "live" },
  published: { txt: "Tistory 발행 완료", cls: "done" },
};

export function Topbar() {
  const {
    toggleSidebar,
    toggleRightPanel,
    activeArticle,
    pipelineMode,
    openGateModal,
    gateModal,
    theme,
    setTheme,
    setPublishKitOpen,
  } = useAppStore();

  const stage = STAGE_LABELS[pipelineMode] ?? { txt: "준비", cls: "" };
  const isGateMode = pipelineMode === "outline" || pipelineMode === "gate2";
  const runId = useAppStore((s) => {
    const ev = s.articles.find((a) => a.id === s.activeArticle?.id);
    return ev?.id ?? 0;
  });

  return (
    <header className="topbar">
      <button className="icon-btn" title="사이드바" onClick={toggleSidebar}>
        <Icons.Sidebar />
      </button>
      <div className="crumbs">
        <span className="crumb">AI의 정석</span>
        <span className="sep">/</span>
        <span className="crumb">Drafts</span>
        <span className="sep">/</span>
        <span className="crumb last">
          {activeArticle
            ? (activeArticle.title ?? activeArticle.topic)
            : "새 글"}
        </span>
      </div>

      <div className="topbar-right">
        {pipelineMode !== "idle" && (
          <button
            className={`pipeline-pill ${stage.cls}`}
            onClick={() => {
              if (isGateMode && gateModal === null) {
                openGateModal(
                  pipelineMode === "outline" ? "gate_one" : "gate_two",
                  runId,
                );
              }
            }}
            title={isGateMode ? "검수 모달 열기" : ""}
          >
            {stage.cls === "live" && <span className="pulse" />}
            {stage.txt}
          </button>
        )}
        <button
          className="icon-btn"
          title="발행 준비"
          disabled={!activeArticle}
          onClick={() => setPublishKitOpen(true)}
        >
          <Icons.Send s={14} /> 발행 준비
        </button>
        <button
          className="icon-btn ghost"
          title={theme === "light" ? "다크 모드" : "라이트 모드"}
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
        >
          {theme === "light" ? <Icons.Moon s={14} /> : <Icons.Sun s={14} />}
        </button>
        <button className="icon-btn primary" onClick={toggleRightPanel}>
          파이프라인
        </button>
        <button className="icon-btn" title="더보기">
          <Icons.More />
        </button>
      </div>
    </header>
  );
}
