import { useCallback, useRef } from "react";
import { usePipelineStore } from "../stores/pipeline-store";
import { useAppStore } from "../stores/app-store";
import type { PipelineEvent } from "../types/pipeline";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface SSECallbacks {
  onRunId?: (runId: number) => void;
  onEvent?: (event: PipelineEvent) => void;
}

export function usePipelineSSE() {
  const abortRef = useRef<AbortController | null>(null);
  const { addEvent, setRunning, setError } = usePipelineStore();
  const { setPipelineMode, openGateModal } = useAppStore();

  const handleEventType = useCallback(
    (event: PipelineEvent) => {
      switch (event.event_type) {
        case "stage_start":
          if (event.stage === "researcher") setPipelineMode("research");
          else if (event.stage === "outliner") setPipelineMode("outline");
          else if (event.stage === "generator") setPipelineMode("generate");
          else if (event.stage === "validator") setPipelineMode("validate");
          break;
        case "gate_pending":
          if (event.stage === "gate_one") {
            setPipelineMode("outline");
            if (event.data?.run_id) {
              openGateModal("gate_one", event.data.run_id as number);
            }
          } else {
            setPipelineMode("gate2");
            if (event.data?.run_id) {
              openGateModal("gate_two", event.data.run_id as number);
            }
          }
          break;
        case "pipeline_complete":
          setPipelineMode("published");
          break;
        case "stage_error":
          setError(event.message);
          break;
      }
    },
    [setPipelineMode, openGateModal, setError],
  );

  const startStream = useCallback(
    async (
      url: string,
      options: RequestInit = {},
      callbacks?: SSECallbacks,
    ) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setRunning(true);
      setError(null);

      try {
        const response = await fetch(`${BASE_URL}${url}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          ...options,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("data:")) {
              const jsonStr = line.slice(5).trim();
              if (!jsonStr) continue;
              try {
                const event = JSON.parse(jsonStr) as PipelineEvent;
                addEvent(event);

                if (event.data?.run_id && callbacks?.onRunId) {
                  callbacks.onRunId(event.data.run_id as number);
                }

                handleEventType(event);
                callbacks?.onEvent?.(event);
              } catch {
                // skip malformed JSON
              }
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          const msg = err instanceof Error ? err.message : "스트리밍 오류";
          setError(msg);
          setPipelineMode("idle");
        }
      } finally {
        setRunning(false);
        abortRef.current = null;
      }
    },
    [addEvent, setRunning, setError, setPipelineMode, handleEventType],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { startStream, abort };
}
