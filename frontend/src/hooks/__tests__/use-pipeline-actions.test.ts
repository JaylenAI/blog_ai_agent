import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePipelineActions } from "../use-pipeline-actions";
import { useArticleStore } from "../../stores/article-store";
import { usePipelineStore } from "../../stores/pipeline-store";

const mockStartStream = vi.fn().mockResolvedValue(undefined);

vi.mock("../use-pipeline-sse", () => ({
  usePipelineSSE: () => ({
    startStream: mockStartStream,
    abort: vi.fn(),
  }),
}));

vi.mock("../../api/client", () => ({
  api: {
    pipeline: {
      reject: vi.fn(),
      getValidations: vi.fn(),
    },
    articles: {
      getContent: vi.fn(),
    },
  },
}));

import { api } from "../../api/client";
const mockReject = vi.mocked(api.pipeline.reject);
const mockGetValidations = vi.mocked(api.pipeline.getValidations);

describe("usePipelineActions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePipelineStore.getState().reset();
    useArticleStore.setState({
      pipelineMode: "idle",
      gateModal: null,
      activeArticle: null,
    });
  });

  it("approveGate closes gate modal and starts SSE stream", async () => {
    useArticleStore.setState({
      gateModal: { gate: "gate_one", runId: 5 },
    });

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.approveGate(5);
    });

    expect(useArticleStore.getState().gateModal).toBeNull();
    expect(mockStartStream).toHaveBeenCalledWith(
      "/pipeline/runs/5/approve/stream",
      {},
      expect.objectContaining({ onEvent: expect.any(Function) }),
    );
  });

  it("rejectGate calls API and resets pipeline mode", async () => {
    mockReject.mockResolvedValueOnce({ success: true, data: { status: "cancelled" } });

    useArticleStore.setState({
      pipelineMode: "outline",
      gateModal: { gate: "gate_one", runId: 3 },
    });

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.rejectGate(3);
    });

    expect(mockReject).toHaveBeenCalledWith(3);
    expect(useArticleStore.getState().pipelineMode).toBe("idle");
    expect(useArticleStore.getState().gateModal).toBeNull();
  });

  it("rejectGate sets error on API failure", async () => {
    mockReject.mockResolvedValueOnce({
      success: false,
      error: "이미 처리됨",
    });

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.rejectGate(3);
    });

    expect(usePipelineStore.getState().error).toBe("이미 처리됨");
  });

  it("rejectGate sets error on network failure", async () => {
    mockReject.mockRejectedValueOnce(new Error("network"));

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.rejectGate(3);
    });

    expect(usePipelineStore.getState().error).toBe("network");
  });

  it("rejectGate resets isRunning in finally block", async () => {
    mockReject.mockRejectedValueOnce(new Error("fail"));

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.rejectGate(1);
    });

    expect(usePipelineStore.getState().isRunning).toBe(false);
  });

  it("fetchValidations stores validation data", async () => {
    const validations = [
      { item: "제목 길이", category: "style", passed: true, score: 1 },
    ];
    const summary = { passed: 1, failed: 0, score: 1 };

    mockGetValidations.mockResolvedValueOnce({
      success: true,
      data: { validations, summary },
    });

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.fetchValidations(10);
    });

    expect(usePipelineStore.getState().validations).toEqual(validations);
    expect(usePipelineStore.getState().validationSummary).toEqual(summary);
  });

  it("fetchValidations handles failure gracefully", async () => {
    mockGetValidations.mockRejectedValueOnce(new Error("fail"));

    const { result } = renderHook(() => usePipelineActions());

    await act(async () => {
      await result.current.fetchValidations(10);
    });

    expect(usePipelineStore.getState().validations).toEqual([]);
  });
});
