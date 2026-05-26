import { useCallback } from "react";
import { api } from "../api/client";
import { useAppStore } from "../stores/app-store";
import { usePipelineStore } from "../stores/pipeline-store";
import { usePipelineSSE } from "./use-pipeline-sse";
import type { PipelineEvent } from "../types/pipeline";

export function usePipelineActions() {
  const { setPipelineMode, closeGateModal, setArticleContent, activeArticle } =
    useAppStore();
  const { setValidations, setRunning, setError } = usePipelineStore();
  const { startStream } = usePipelineSSE();

  const approveGate = useCallback(
    async (runId: number) => {
      await startStream(
        `/pipeline/runs/${runId}/approve/stream`,
        {},
        {
          onEvent: async (event: PipelineEvent) => {
            if (event.event_type === "stage_start") {
              closeGateModal();
            }
            if (
              event.event_type === "gate_pending" &&
              event.stage === "gate_two" &&
              activeArticle
            ) {
              const content = await api.articles.getContent(activeArticle.id);
              if (content) setArticleContent(content);
            }
          },
        },
      );
    },
    [startStream, closeGateModal, activeArticle, setArticleContent],
  );

  const rejectGate = useCallback(
    async (runId: number) => {
      setRunning(true);
      try {
        const res = await api.pipeline.reject(runId);
        if (!res.success) {
          throw new Error(res.error ?? "거부 실패");
        }
        setPipelineMode("idle");
        closeGateModal();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "알 수 없는 오류";
        setError(msg);
      } finally {
        setRunning(false);
      }
    },
    [setRunning, setError, setPipelineMode, closeGateModal],
  );

  const rejectAndRevise = useCallback(
    async (runId: number, feedback: string) => {
      closeGateModal();

      await startStream(
        `/pipeline/runs/${runId}/reject-and-revise/stream`,
        { body: JSON.stringify({ feedback }) },
      );
    },
    [startStream, closeGateModal],
  );

  const fetchValidations = useCallback(
    async (runId: number) => {
      try {
        const res = await api.pipeline.getValidations(runId);
        if (res.success && res.data) {
          setValidations(res.data.validations, res.data.summary);
        }
      } catch {
        /* validation fetch 실패는 치명적이지 않음 */
      }
    },
    [setValidations],
  );

  return { approveGate, rejectGate, rejectAndRevise, fetchValidations };
}
