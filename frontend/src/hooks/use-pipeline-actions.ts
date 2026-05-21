import { useCallback } from "react";
import { api } from "../api/client";
import { useAppStore } from "../stores/app-store";
import { usePipelineStore } from "../stores/pipeline-store";
import type { PipelineEvent } from "../types/pipeline";

export function usePipelineActions() {
  const { setPipelineMode, closeGateModal, setArticleContent, activeArticle } =
    useAppStore();
  const { setEvents, setValidations, setRunning, setError, events } =
    usePipelineStore();

  const approveGate = useCallback(
    async (runId: number) => {
      setRunning(true);
      setError(null);
      try {
        const res = await api.pipeline.approve(runId);
        if (!res.success || !res.data) {
          throw new Error(res.error ?? "승인 실패");
        }

        const newEvents = res.data.events as PipelineEvent[];
        setEvents([...events, ...newEvents]);

        const lastEvent = newEvents[newEvents.length - 1];
        if (lastEvent?.event_type === "gate_pending") {
          setPipelineMode(
            lastEvent.stage === "gate_one" ? "outline" : "gate2",
          );
        } else if (lastEvent?.event_type === "pipeline_complete") {
          setPipelineMode("published");
        } else if (lastEvent?.event_type === "stage_error") {
          setError(lastEvent.message);
        }

        closeGateModal();

        if (activeArticle) {
          const content = await api.articles.getContent(activeArticle.id);
          if (content) {
            setArticleContent(content);
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "알 수 없는 오류";
        setError(msg);
      } finally {
        setRunning(false);
      }
    },
    [
      events,
      setEvents,
      setRunning,
      setError,
      setPipelineMode,
      closeGateModal,
      activeArticle,
      setArticleContent,
    ],
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

  return { approveGate, rejectGate, fetchValidations };
}
