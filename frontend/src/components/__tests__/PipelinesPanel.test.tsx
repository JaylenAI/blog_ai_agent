import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { PipelinesPanel } from "../panels/PipelinesPanel";
import type { PipelineRun } from "../../types/pipeline";

const mockListRuns = vi.fn();
const mockCancel = vi.fn();

vi.mock("../../api/client", () => ({
  api: {
    pipeline: {
      listRuns: (...args: unknown[]) => mockListRuns(...args),
      cancel: (...args: unknown[]) => mockCancel(...args),
    },
  },
}));

const mockStartStream = vi.fn();
vi.mock("../../hooks/use-pipeline-sse", () => ({
  usePipelineSSE: () => ({ startStream: mockStartStream }),
}));

function makeRun(overrides: Partial<PipelineRun> = {}): PipelineRun {
  return {
    id: 1,
    article_id: 1,
    current_stage: "router",
    status: "running",
    started_at: "2026-01-01T00:00:00",
    completed_at: null,
    ...overrides,
  };
}

describe("PipelinesPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListRuns.mockResolvedValue({ success: true, data: [] });
  });

  it("renders loading state initially", () => {
    mockListRuns.mockReturnValue(new Promise(() => {}));

    render(<PipelinesPanel />);
    expect(screen.getByText("실행 이력 불러오는 중...")).toBeInTheDocument();
  });

  it("renders empty state when no runs", async () => {
    mockListRuns.mockResolvedValue({ success: true, data: [] });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("실행 이력이 없습니다.")).toBeInTheDocument();
    });
  });

  it("renders error state with retry button on fetch failure", async () => {
    mockListRuns.mockRejectedValue(new Error("Network error"));

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(
        screen.getByText("실행 이력을 불러올 수 없습니다."),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("다시 시도")).toBeInTheDocument();
  });

  it("retries fetch when retry button is clicked", async () => {
    mockListRuns.mockRejectedValueOnce(new Error("Network error"));
    mockListRuns.mockResolvedValueOnce({ success: true, data: [] });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("다시 시도")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("다시 시도"));
    expect(mockListRuns).toHaveBeenCalledTimes(2);
  });

  it("renders pipeline run table with data", async () => {
    mockListRuns.mockResolvedValue({
      success: true,
      data: [
        makeRun({ id: 10, status: "running", current_stage: "researcher" }),
        makeRun({ id: 11, status: "completed", current_stage: "publisher" }),
      ],
    });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("#10")).toBeInTheDocument();
      expect(screen.getByText("#11")).toBeInTheDocument();
    });
    expect(screen.getByText("researcher")).toBeInTheDocument();
    expect(screen.getByText("publisher")).toBeInTheDocument();
  });

  it("renders status labels in Korean", async () => {
    mockListRuns.mockResolvedValue({
      success: true,
      data: [
        makeRun({ id: 1, status: "running" }),
        makeRun({ id: 2, status: "completed" }),
        makeRun({ id: 3, status: "failed" }),
      ],
    });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("실행 중")).toBeInTheDocument();
      expect(screen.getByText("완료")).toBeInTheDocument();
      expect(screen.getByText("실패")).toBeInTheDocument();
    });
  });

  it("renders cancel button for running and paused runs", async () => {
    mockListRuns.mockResolvedValue({
      success: true,
      data: [
        makeRun({ id: 1, status: "running" }),
        makeRun({ id: 2, status: "paused" }),
        makeRun({ id: 3, status: "completed" }),
      ],
    });

    render(<PipelinesPanel />);
    await waitFor(() => {
      const cancelButtons = screen.getAllByText("취소");
      expect(cancelButtons).toHaveLength(2);
    });
  });

  it("renders retry button for failed runs", async () => {
    mockListRuns.mockResolvedValue({
      success: true,
      data: [makeRun({ id: 5, status: "failed" })],
    });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("재시도")).toBeInTheDocument();
    });
  });

  it("renders table headers", async () => {
    mockListRuns.mockResolvedValue({
      success: true,
      data: [makeRun()],
    });

    render(<PipelinesPanel />);
    await waitFor(() => {
      expect(screen.getByText("ID")).toBeInTheDocument();
      expect(screen.getByText("상태")).toBeInTheDocument();
      expect(screen.getByText("스테이지")).toBeInTheDocument();
      expect(screen.getByText("시작 시간")).toBeInTheDocument();
    });
  });
});
