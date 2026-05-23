import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RightPanel } from "../layout/RightPanel";
import { useUIStore } from "../../stores/ui-store";
import { useArticleStore } from "../../stores/article-store";

vi.mock("../tabs", () => ({
  PipelineTab: () => <div data-testid="tab-pipeline" />,
  ReferencesTab: () => <div data-testid="tab-references" />,
  ValidationTab: () => <div data-testid="tab-validation" />,
  HistoryTab: () => <div data-testid="tab-history" />,
}));

vi.mock("../common/Icons", () => ({
  Icons: {
    Layers: ({ s: _s }: { s?: number }) => (
      <span data-testid="icon-layers" />
    ),
    Tag: ({ s: _s }: { s?: number }) => <span data-testid="icon-tag" />,
    CheckCircle: ({ s: _s }: { s?: number }) => (
      <span data-testid="icon-check" />
    ),
  },
}));

describe("RightPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useUIStore.setState({
      rightPanelTab: "pipeline",
      rightPanelOpen: true,
    });
    useArticleStore.setState({
      pipelineMode: "idle",
    });
  });

  it("기본 탭(파이프라인)을 렌더링한다", () => {
    render(<RightPanel />);
    expect(screen.getByTestId("tab-pipeline")).toBeInTheDocument();
    expect(screen.getByText("파이프라인")).toBeInTheDocument();
  });

  it("자료 탭으로 전환한다", () => {
    render(<RightPanel />);

    fireEvent.click(screen.getByText("자료"));

    expect(useUIStore.getState().rightPanelTab).toBe("references");
    expect(screen.getByTestId("tab-references")).toBeInTheDocument();
  });

  it("검증 탭으로 전환한다", () => {
    render(<RightPanel />);

    fireEvent.click(screen.getByText("검증"));

    expect(useUIStore.getState().rightPanelTab).toBe("validation");
    expect(screen.getByTestId("tab-validation")).toBeInTheDocument();
  });

  it("히스토리 탭으로 전환한다", () => {
    render(<RightPanel />);

    fireEvent.click(screen.getByText("히스토리"));

    expect(useUIStore.getState().rightPanelTab).toBe("history");
    expect(screen.getByTestId("tab-history")).toBeInTheDocument();
  });

  it("활성 탭에 active 클래스가 적용된다", () => {
    useUIStore.setState({ rightPanelTab: "validation" });

    render(<RightPanel />);

    const validationTab = screen.getByText("검증").closest("button");
    expect(validationTab?.className).toContain("active");

    const pipelineTab = screen.getByText("파이프라인").closest("button");
    expect(pipelineTab?.className).not.toContain("active");
  });

  it("pipelineMode가 validate로 바뀌면 validation 탭으로 자동 전환된다", () => {
    useUIStore.setState({ rightPanelTab: "pipeline" });

    const { rerender } = render(<RightPanel />);
    expect(useUIStore.getState().rightPanelTab).toBe("pipeline");

    useArticleStore.setState({ pipelineMode: "validate" });
    rerender(<RightPanel />);

    expect(useUIStore.getState().rightPanelTab).toBe("validation");
  });

  it("pipelineMode가 research로 바뀌면 pipeline 탭으로 자동 전환된다", () => {
    useUIStore.setState({ rightPanelTab: "references" });

    const { rerender } = render(<RightPanel />);
    expect(useUIStore.getState().rightPanelTab).toBe("references");

    useArticleStore.setState({ pipelineMode: "research" });
    rerender(<RightPanel />);

    expect(useUIStore.getState().rightPanelTab).toBe("pipeline");
  });

  it("className prop이 전달된다", () => {
    const { container } = render(<RightPanel className="custom-cls" />);
    const aside = container.querySelector("aside");
    expect(aside?.className).toContain("custom-cls");
    expect(aside?.className).toContain("right-panel");
  });
});
