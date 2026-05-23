import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { usePipelineSSE } from "../../hooks/use-pipeline-sse";
import type { PipelineRun } from "../../types/pipeline";
import { STATUS_LABELS, formatTime } from "./shared";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { ErrorState } from "../common/ErrorState";

export function PipelinesPanel() {
  const addToast = useAppStore((s) => s.addToast);
  const setSidebarPanel = useAppStore((s) => s.setSidebarPanel);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const { startStream } = usePipelineSSE();

  const fetchRuns = useCallback(() => {
    setLoading(true);
    setFetchError(false);
    api.pipeline
      .listRuns(undefined, 50)
      .then((res) => {
        if (res.success && res.data) setRuns(res.data);
      })
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  const handleCancel = useCallback(
    async (runId: number) => {
      try {
        await api.pipeline.cancel(runId);
        addToast({ type: "success", message: `Run #${runId} 취소 완료` });
        fetchRuns();
      } catch {
        addToast({ type: "error", message: "취소 실패" });
      }
    },
    [addToast, fetchRuns],
  );

  const handleRetry = useCallback(
    (runId: number) => {
      setSidebarPanel(null);
      startStream(`/pipeline/runs/${runId}/retry/stream`);
    },
    [setSidebarPanel, startStream],
  );

  if (loading) return <LoadingSpinner message="실행 이력 불러오는 중..." />;
  if (fetchError) return <ErrorState message="실행 이력을 불러올 수 없습니다." onRetry={fetchRuns} />;
  if (runs.length === 0)
    return <div className="sb-panel-empty">실행 이력이 없습니다.</div>;

  return (
    <div className="sb-panel-table-wrap">
      <table className="sb-panel-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>상태</th>
            <th>스테이지</th>
            <th>시작 시간</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id}>
              <td>#{r.id}</td>
              <td>
                <span className={`run-status run-status--${r.status}`}>
                  {STATUS_LABELS[r.status] ?? r.status}
                </span>
              </td>
              <td>{r.current_stage}</td>
              <td>{formatTime(r.started_at)}</td>
              <td>
                {(r.status === "running" || r.status === "paused") && (
                  <button
                    className="run-cancel-btn"
                    onClick={() => handleCancel(r.id)}
                    title="실행 취소"
                  >
                    취소
                  </button>
                )}
                {r.status === "failed" && (
                  <button
                    className="run-retry-btn"
                    onClick={() => handleRetry(r.id)}
                    title="재시도"
                  >
                    재시도
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
