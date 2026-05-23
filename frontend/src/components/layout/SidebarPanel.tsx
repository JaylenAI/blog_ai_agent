import { useEffect } from "react";
import { useAppStore, type SidebarPanel as PanelType } from "../../stores/app-store";
import { Icons } from "../common/Icons";
import {
  DashboardPanel,
  PipelinesPanel,
  SettingsPanel,
  StyleGuidePanel,
  TistoryPanel,
  SubagentsPanel,
  SkillsPanel,
  EvalPanel,
  McpPanel,
} from "../panels";

const PANEL_TITLES: Record<NonNullable<PanelType>, string> = {
  dashboard: "블로그 대시보드",
  settings: "종합 설정",
  pipelines: "파이프라인 실행 이력",
  "style-guide": "STYLE.md",
  tistory: "Tistory 연결",
  subagents: "Subagents",
  skills: "Skills",
  eval: "Eval Harness",
  mcp: "MCP & API",
};

function PanelContent({ panel }: { panel: NonNullable<PanelType> }) {
  switch (panel) {
    case "dashboard":
      return <DashboardPanel />;
    case "settings":
      return <SettingsPanel />;
    case "pipelines":
      return <PipelinesPanel />;
    case "style-guide":
      return <StyleGuidePanel />;
    case "tistory":
      return <TistoryPanel />;
    case "subagents":
      return <SubagentsPanel />;
    case "skills":
      return <SkillsPanel />;
    case "eval":
      return <EvalPanel />;
    case "mcp":
      return <McpPanel />;
    default:
      return (
        <div className="sb-panel-placeholder">
          <Icons.Beaker s={32} w={1} />
          <p>{PANEL_TITLES[panel]}</p>
          <span>개발 예정</span>
        </div>
      );
  }
}

export function SidebarPanel() {
  const { sidebarPanel, setSidebarPanel } = useAppStore();

  useEffect(() => {
    if (!sidebarPanel) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSidebarPanel(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [sidebarPanel, setSidebarPanel]);

  if (!sidebarPanel) return null;

  return (
    <div
      className="sb-panel-overlay"
      onClick={() => setSidebarPanel(null)}
    >
      <div className="sb-panel" onClick={(e) => e.stopPropagation()}>
        <div className="sb-panel-header">
          <span className="sb-panel-title">
            {PANEL_TITLES[sidebarPanel]}
          </span>
          <button
            className="sb-panel-close"
            onClick={() => setSidebarPanel(null)}
            aria-label="닫기"
          >
            <Icons.X s={14} />
          </button>
        </div>
        <div className="sb-panel-body">
          <PanelContent panel={sidebarPanel} />
        </div>
      </div>
    </div>
  );
}
