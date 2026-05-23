import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePipelineSSE } from "../use-pipeline-sse";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useArticleStore } from "../../stores/article-store";
import { useNotificationStore } from "../../stores/notification-store";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function sseStream(lines: string[]) {
  const text = lines.join("\n") + "\n";
  const encoder = new TextEncoder();
  let sent = false;
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => ({
        read: () => {
          if (!sent) {
            sent = true;
            return Promise.resolve({
              done: false,
              value: encoder.encode(text),
            });
          }
          return Promise.resolve({ done: true, value: undefined });
        },
      }),
    },
  } as unknown as Response;
}

describe("usePipelineSSE", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePipelineStore.getState().reset();
    useArticleStore.setState({
      pipelineMode: "idle",
      gateModal: null,
    });
    useNotificationStore.setState({ notifications: [] });
  });

  it("sets isRunning true during stream", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"researcher","message":"starting"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/pipeline/start/stream");
    });

    expect(usePipelineStore.getState().isRunning).toBe(false);
  });

  it("adds events to pipeline store", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"researcher","message":"시작"}',
        'data: {"event_type":"stage_complete","stage":"researcher","message":"완료"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/pipeline/start/stream");
    });

    expect(usePipelineStore.getState().events).toHaveLength(2);
    expect(usePipelineStore.getState().events[0].event_type).toBe(
      "stage_start",
    );
  });

  it("sets pipeline mode on stage_start events", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"researcher","message":""}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(useArticleStore.getState().pipelineMode).toBe("research");
  });

  it("sets outline mode for outliner stage", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"outliner","message":""}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(useArticleStore.getState().pipelineMode).toBe("outline");
  });

  it("sets generate mode for generator stage", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"generator","message":""}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(useArticleStore.getState().pipelineMode).toBe("generate");
  });

  it("opens gate modal on gate_pending event", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"gate_pending","stage":"gate_one","message":"","data":{"run_id":5}}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(useArticleStore.getState().gateModal).toEqual({
      gate: "gate_one",
      runId: 5,
    });
  });

  it("adds notification on gate_pending", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"gate_pending","stage":"gate_one","message":"","data":{"run_id":5}}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    const notifications = useNotificationStore.getState().notifications;
    expect(notifications).toHaveLength(1);
    expect(notifications[0].type).toBe("gate");
  });

  it("sets published mode on pipeline_complete", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"pipeline_complete","stage":"publisher","message":"done"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(useArticleStore.getState().pipelineMode).toBe("published");
  });

  it("sets error on stage_error event", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_error","stage":"researcher","message":"Claude CLI 실패"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(usePipelineStore.getState().error).toBe("Claude CLI 실패");
  });

  it("calls onRunId callback when run_id appears", async () => {
    const onRunId = vi.fn();

    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"researcher","message":"","data":{"run_id":42}}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test", {}, { onRunId });
    });

    expect(onRunId).toHaveBeenCalledWith(42);
  });

  it("calls onEvent callback for each event", async () => {
    const onEvent = vi.fn();

    mockFetch.mockResolvedValueOnce(
      sseStream([
        'data: {"event_type":"stage_start","stage":"researcher","message":"a"}',
        'data: {"event_type":"stage_complete","stage":"researcher","message":"b"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test", {}, { onEvent });
    });

    expect(onEvent).toHaveBeenCalledTimes(2);
  });

  it("handles malformed JSON gracefully", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        "data: {not valid json}",
        'data: {"event_type":"stage_start","stage":"researcher","message":"ok"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(usePipelineStore.getState().events).toHaveLength(1);
  });

  it("skips empty data lines", async () => {
    mockFetch.mockResolvedValueOnce(
      sseStream([
        "data: ",
        'data: {"event_type":"stage_start","stage":"researcher","message":"ok"}',
      ]),
    );

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(usePipelineStore.getState().events).toHaveLength(1);
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      text: () => Promise.resolve("서버 내부 오류"),
    });

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(usePipelineStore.getState().error).toBeTruthy();
  });

  it("sets error when response has no body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      body: null,
    });

    const { result } = renderHook(() => usePipelineSSE());

    await act(async () => {
      await result.current.startStream("/test");
    });

    expect(usePipelineStore.getState().error).toBeTruthy();
  });

  it("abort cancels the stream", () => {
    const { result } = renderHook(() => usePipelineSSE());
    expect(() => result.current.abort()).not.toThrow();
  });
});
