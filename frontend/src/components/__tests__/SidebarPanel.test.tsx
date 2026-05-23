import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SidebarPanel } from "../layout/SidebarPanel";
import { useUIStore } from "../../stores/ui-store";

vi.mock("../panels", () => ({
  DashboardPanel: () => <div data-testid="panel-dashboard" />,
  PipelinesPanel: () => <div data-testid="panel-pipelines" />,
  SettingsPanel: () => <div data-testid="panel-settings" />,
  StyleGuidePanel: () => <div data-testid="panel-style-guide" />,
  TistoryPanel: () => <div data-testid="panel-tistory" />,
  SubagentsPanel: () => <div data-testid="panel-subagents" />,
  SkillsPanel: () => <div data-testid="panel-skills" />,
  EvalPanel: () => <div data-testid="panel-eval" />,
  McpPanel: () => <div data-testid="panel-mcp" />,
}));

vi.mock("../common/Icons", () => ({
  Icons: {
    X: ({ s: _s }: { s?: number }) => <span data-testid="icon-x" />,
    Beaker: ({ s: _s, w: _w }: { s?: number; w?: number }) => (
      <span data-testid="icon-beaker" />
    ),
  },
}));

describe("SidebarPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useUIStore.setState({ sidebarPanel: null });
  });

  it("sidebarPanel이 null일 때 아무것도 렌더링하지 않는다", () => {
    const { container } = render(<SidebarPanel />);
    expect(container.innerHTML).toBe("");
  });

  it("dashboard 패널을 올바르게 렌더링한다", () => {
    useUIStore.setState({ sidebarPanel: "dashboard" });

    render(<SidebarPanel />);
    expect(screen.getByText("블로그 대시보드")).toBeInTheDocument();
    expect(screen.getByTestId("panel-dashboard")).toBeInTheDocument();
  });

  it("pipelines 패널을 올바르게 렌더링한다", () => {
    useUIStore.setState({ sidebarPanel: "pipelines" });

    render(<SidebarPanel />);
    expect(screen.getByText("파이프라인 실행 이력")).toBeInTheDocument();
    expect(screen.getByTestId("panel-pipelines")).toBeInTheDocument();
  });

  it("settings 패널을 올바르게 렌더링한다", () => {
    useUIStore.setState({ sidebarPanel: "settings" });

    render(<SidebarPanel />);
    expect(screen.getByText("종합 설정")).toBeInTheDocument();
    expect(screen.getByTestId("panel-settings")).toBeInTheDocument();
  });

  it("style-guide 패널을 올바르게 렌더링한다", () => {
    useUIStore.setState({ sidebarPanel: "style-guide" });

    render(<SidebarPanel />);
    expect(screen.getByText("STYLE.md")).toBeInTheDocument();
    expect(screen.getByTestId("panel-style-guide")).toBeInTheDocument();
  });

  it("닫기 버튼 클릭 시 패널이 닫힌다", () => {
    useUIStore.setState({ sidebarPanel: "dashboard" });

    render(<SidebarPanel />);

    const closeBtn = screen.getByLabelText("닫기");
    fireEvent.click(closeBtn);

    expect(useUIStore.getState().sidebarPanel).toBeNull();
  });

  it("overlay 클릭 시 패널이 닫힌다", () => {
    useUIStore.setState({ sidebarPanel: "tistory" });

    render(<SidebarPanel />);

    const overlay = document.querySelector(".sb-panel-overlay")!;
    fireEvent.click(overlay);

    expect(useUIStore.getState().sidebarPanel).toBeNull();
  });

  it("패널 본문 클릭 시 닫히지 않는다 (stopPropagation)", () => {
    useUIStore.setState({ sidebarPanel: "skills" });

    render(<SidebarPanel />);

    const panelBody = document.querySelector(".sb-panel")!;
    fireEvent.click(panelBody);

    expect(useUIStore.getState().sidebarPanel).not.toBeNull();
  });

  it("Escape 키로 패널이 닫힌다", () => {
    useUIStore.setState({ sidebarPanel: "eval" });

    render(<SidebarPanel />);
    expect(screen.getByText("Eval Harness")).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "Escape" });

    expect(useUIStore.getState().sidebarPanel).toBeNull();
  });
});
