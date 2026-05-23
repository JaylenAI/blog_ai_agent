import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { PipelineTab } from "../tabs/PipelineTab";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useArticleStore } from "../../stores/article-store";
import type { PipelineEvent } from "../../types/pipeline";

function makeEvent(
  overrides: Partial<PipelineEvent> & Pick<PipelineEvent, "event_type" | "stage">,
): PipelineEvent {
  return {
    message: "",
    data: {},
    ...overrides,
  };
}

describe("PipelineTab", () => {
  beforeEach(() => {
    usePipelineStore.setState({
      events: [],
      validations: [],
      validationSummary: null,
    });
    useArticleStore.setState({
      gateModal: null,
    });
  });

  it("renders all pipeline stage names", () => {
    render(<PipelineTab />);
    expect(screen.getByText("Router")).toBeInTheDocument();
    expect(screen.getByText("Researcher")).toBeInTheDocument();
    expect(screen.getByText("Outliner")).toBeInTheDocument();
    expect(screen.getByText("Gate 1")).toBeInTheDocument();
    expect(screen.getByText("Generator")).toBeInTheDocument();
    expect(screen.getByText("Validator")).toBeInTheDocument();
    expect(screen.getByText("Gate 2")).toBeInTheDocument();
    expect(screen.getByText("Publisher")).toBeInTheDocument();
  });

  it("shows stage descriptions", () => {
    render(<PipelineTab />);
    expect(
      screen.getByText(/주제 분석 · 키워드 추출 · 분량 결정/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/4-channel 자료수집/),
    ).toBeInTheDocument();
  });

  it("marks completed stages with done class", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "stage_start",
          stage: "router",
          message: "Router started",
        }),
        makeEvent({
          event_type: "stage_complete",
          stage: "router",
          message: "Router done",
        }),
      ],
    });

    const { container } = render(<PipelineTab />);
    const routerStage = container.querySelector(".pl-stage.done");
    expect(routerStage).toBeInTheDocument();
  });

  it("marks active stages correctly", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "stage_start",
          stage: "router",
          message: "Router started",
        }),
      ],
    });

    const { container } = render(<PipelineTab />);
    const activeStage = container.querySelector(".pl-stage.active");
    expect(activeStage).toBeInTheDocument();
  });

  it("marks error stages with error class", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "stage_error",
          stage: "router",
          message: "Router failed",
        }),
      ],
    });

    const { container } = render(<PipelineTab />);
    const errorStage = container.querySelector(".pl-stage.error");
    expect(errorStage).toBeInTheDocument();
  });

  it("shows gate button when gate_pending event exists", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "gate_pending",
          stage: "gate_one",
          message: "Outline ready",
          data: { run_id: 42 },
        }),
      ],
    });

    render(<PipelineTab />);
    expect(screen.getByText("아웃라인 검수 열기")).toBeInTheDocument();
  });

  it("shows gate 2 button text for gate_two", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "gate_pending",
          stage: "gate_two",
          message: "Final review",
          data: { run_id: 10 },
        }),
      ],
    });

    render(<PipelineTab />);
    expect(screen.getByText("최종 검수 열기")).toBeInTheDocument();
  });

  it("displays librarian cards when researcher is active", () => {
    usePipelineStore.setState({
      events: [
        makeEvent({
          event_type: "stage_start",
          stage: "researcher",
          message: "Research started",
        }),
      ],
    });

    render(<PipelineTab />);
    expect(screen.getByText("librarian-official")).toBeInTheDocument();
    expect(screen.getByText("librarian-github")).toBeInTheDocument();
    expect(screen.getByText("librarian-blog-en")).toBeInTheDocument();
    expect(screen.getByText("librarian-blog-kr")).toBeInTheDocument();
  });
});
