import { useCallback } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useArticles } from "../../hooks/use-articles";
import { api } from "../../api/client";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { RightPanel } from "./RightPanel";
import { Launcher } from "../editor/Launcher";
import { Editor } from "../editor/Editor";
import { GateModal } from "../gate/GateModal";
import { PipelineProgress } from "../common/PipelineProgress";
import type { Article } from "../../types/article";
import type { PipelineEvent } from "../../types/pipeline";

export function AppShell() {
  const {
    sidebarOpen,
    rightPanelOpen,
    activeArticle,
    gateModal,
    setPipelineMode,
    setActiveArticle,
    addArticle,
    openGateModal,
    closeGateModal,
    setArticleContent,
  } = useAppStore();

  const { setRunning, setEvents, setError } = usePipelineStore();
  const { refetch } = useArticles();

  const handleStart = useCallback(
    async (topic: string, autoGateOne: boolean) => {
      setRunning(true);
      setError(null);
      setPipelineMode("research");

      try {
        const createRes = await api.articles.create(topic);
        if (!createRes.success || !createRes.data) {
          throw new Error(createRes.error ?? "글 생성 실패");
        }
        const article = createRes.data as Article;
        addArticle(article);
        setActiveArticle(article);

        const pipelineRes = await api.pipeline.start(article.id, autoGateOne);
        if (!pipelineRes.success || !pipelineRes.data) {
          throw new Error(pipelineRes.error ?? "파이프라인 시작 실패");
        }

        const events = pipelineRes.data.events as PipelineEvent[];
        const runId = pipelineRes.data.run_id;
        setEvents(events);

        const lastEvent = events[events.length - 1];
        if (lastEvent?.event_type === "gate_pending") {
          if (lastEvent.stage === "gate_one") {
            setPipelineMode("outline");
            openGateModal("gate_one", runId);
          } else {
            setPipelineMode("gate2");
            openGateModal("gate_two", runId);

            const content = await api.articles.getContent(article.id);
            if (content) setArticleContent(content);
          }
        } else if (lastEvent?.event_type === "pipeline_complete") {
          setPipelineMode("published");
        } else if (lastEvent?.event_type === "stage_error") {
          setPipelineMode("idle");
          setError(lastEvent.message);
        }

        void refetch();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "알 수 없는 오류";
        setError(msg);
        setPipelineMode("idle");
      } finally {
        setRunning(false);
      }
    },
    [
      setPipelineMode,
      setActiveArticle,
      addArticle,
      setRunning,
      setEvents,
      setError,
      openGateModal,
      setArticleContent,
      refetch,
    ],
  );

  const isRunning = usePipelineStore((s) => s.isRunning);
  const error = usePipelineStore((s) => s.error);

  return (
    <div className="flex w-full h-dvh overflow-hidden">
      {sidebarOpen && <Sidebar />}

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar />
        <PipelineProgress />

        {error && (
          <div
            className="px-4 py-2 text-sm"
            style={{
              backgroundColor:
                "color-mix(in oklch, var(--color-danger) 10%, transparent)",
              color: "var(--color-danger)",
            }}
          >
            {error}
          </div>
        )}

        {activeArticle ? (
          <Editor article={activeArticle} />
        ) : (
          <Launcher onStart={handleStart} disabled={isRunning} />
        )}
      </div>

      {rightPanelOpen && <RightPanel />}

      {gateModal && (
        <GateModal
          gate={gateModal.gate}
          runId={gateModal.runId}
          onClose={closeGateModal}
        />
      )}
    </div>
  );
}
