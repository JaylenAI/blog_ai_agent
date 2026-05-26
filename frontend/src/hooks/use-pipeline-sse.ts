import { useCallback, useRef } from "react";
import { usePipelineStore } from "../stores/pipeline-store";
import { useAppStore } from "../stores/app-store";
import { useNotificationStore } from "../stores/notification-store";
import type { PipelineEvent } from "../types/pipeline";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface SSECallbacks {
  onRunId?: (runId: number) => void;
  onEvent?: (event: PipelineEvent) => void;
}

export function usePipelineSSE() {
  const abortRef = useRef<AbortController | null>(null);
  const { addEvent, setRunning, setError } = usePipelineStore();
  const { setPipelineMode, openGateModal, addToast } = useAppStore();
  const addNotification = useNotificationStore((s) => s.addNotification);

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
          addNotification({
            type: "gate",
            title: event.stage === "gate_one" ? "Gate 1 검수 대기" : "Gate 2 검수 대기",
            message: "아웃라인/최종 글을 확인해 주세요",
            runId: event.data?.run_id as number | undefined,
          });
          break;
        case "pipeline_complete":
          setPipelineMode("published");
          addToast({ type: "success", message: "파이프라인 완료 — 발행 준비 됐습니다" });
          addNotification({
            type: "complete",
            title: "파이프라인 완료",
            message: "발행 준비가 완료되었습니다",
          });
          break;
        case "stage_error":
          setError(event.message);
          addToast({ type: "error", message: `스테이지 오류: ${event.message}` });
          addNotification({
            type: "error",
            title: "스테이지 오류",
            message: event.message,
          });
          break;
        case "pipeline_error":
          setError(event.message);
          addToast({ type: "error", message: `파이프라인 오류: ${event.message}` });
          addNotification({
            type: "error",
            title: "파이프라인 오류",
            message: event.message,
          });
          break;
      }
    },
    [setPipelineMode, openGateModal, setError, addToast, addNotification],
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
      let retried = false;

      try {
        const response = await fetch(`${BASE_URL}${url}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          ...options,
        });

        if (!response.ok) {
          const errorText = await response.text().catch(() => "");
          throw new Error(
            `서버 응답 오류 (${response.status}): ${errorText.slice(0, 200) || response.statusText}`,
          );
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("응답 스트림 없음");

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
              } catch (parseErr) {
                if (import.meta.env.DEV) {
                  console.warn("[SSE] malformed JSON:", jsonStr, parseErr);
                }
              }
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") return;

        const msg = err instanceof Error ? err.message : "스트리밍 오류";
        const delays = [1500, 3000, 6000];

        for (let attempt = 0; attempt < delays.length; attempt++) {
          if (retried && attempt === 0) continue;
          retried = true;
          addToast({ type: "info", message: `연결이 끊겼습니다. 재연결 중... (${attempt + 1}/${delays.length})` });
          await new Promise((r) => setTimeout(r, delays[attempt]));
          try {
            const retryRes = await fetch(`${BASE_URL}${url}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              signal: controller.signal,
              ...options,
            });
            if (retryRes?.ok && retryRes.body) {
              const retryReader = retryRes.body.getReader();
              const retryDecoder = new TextDecoder();
              let retryBuf = "";
              while (true) {
                const { done, value } = await retryReader.read();
                if (done) break;
                retryBuf += retryDecoder.decode(value, { stream: true });
                const lines = retryBuf.split("\n");
                retryBuf = lines.pop() ?? "";
                for (const line of lines) {
                  if (!line.startsWith("data:")) continue;
                  const jsonStr = line.slice(5).trim();
                  if (!jsonStr) continue;
                  try {
                    const event = JSON.parse(jsonStr) as PipelineEvent;
                    addEvent(event);
                    if (event.data?.run_id && callbacks?.onRunId) callbacks.onRunId(event.data.run_id as number);
                    handleEventType(event);
                    callbacks?.onEvent?.(event);
                  } catch {
                    /* malformed JSON — skip */
                  }
                }
              }
              addToast({ type: "success", message: "재연결 성공" });
              return;
            }
          } catch {
            /* retry failed, try next */
          }
        }

        setError(msg);
        setPipelineMode("idle");
        addToast({ type: "error", message: msg });
      } finally {
        setRunning(false);
        abortRef.current = null;
      }
    },
    [addEvent, setRunning, setError, setPipelineMode, handleEventType, addToast],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { startStream, abort };
}
