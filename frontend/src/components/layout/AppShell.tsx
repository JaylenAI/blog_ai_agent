import { lazy, Suspense, useCallback, useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useArticles } from "../../hooks/use-articles";
import { usePipelineSSE } from "../../hooks/use-pipeline-sse";
import { useRestorePipeline } from "../../hooks/use-restore-pipeline";
import { api } from "../../api/client";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { Launcher } from "../editor/Launcher";
import type { Article } from "../../types/article";
import type { PipelineEvent } from "../../types/pipeline";

const Editor = lazy(() =>
  import("../editor/Editor").then((m) => ({ default: m.Editor })),
);
const GateModal = lazy(() =>
  import("../gate/GateModal").then((m) => ({ default: m.GateModal })),
);
const RightPanel = lazy(() =>
  import("./RightPanel").then((m) => ({ default: m.RightPanel })),
);

export function AppShell() {
  const {
    sidebarOpen,
    rightPanelOpen,
    activeArticle,
    gateModal,
    setPipelineMode,
    setActiveArticle,
    addArticle,
    closeGateModal,
    setArticleContent,
  } = useAppStore();

  const theme = useAppStore((s) => s.theme);
  const density = useAppStore((s) => s.density);
  const accentHue = useAppStore((s) => s.accentHue);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    if (density !== "default") {
      root.setAttribute("data-density", density);
    } else {
      root.removeAttribute("data-density");
    }
    root.style.setProperty("--accent", `oklch(55% 0.13 ${accentHue})`);
    root.style.setProperty("--accent-soft", `oklch(55% 0.13 ${accentHue} / 0.10)`);
    root.style.setProperty("--accent-strong", `oklch(45% 0.16 ${accentHue})`);
  }, [theme, density, accentHue]);

  const { setError } = usePipelineStore();
  const { refetch } = useArticles();
  const { startStream } = usePipelineSSE();
  useRestorePipeline();

  const handleStart = useCallback(
    async (topic: string, autoGateOne: boolean) => {
      setPipelineMode("research");

      try {
        const createRes = await api.articles.create(topic);
        if (!createRes.success || !createRes.data) {
          throw new Error(createRes.error ?? "글 생성 실패");
        }
        const article = createRes.data as Article;
        addArticle(article);
        setActiveArticle(article);

        await startStream(
          "/pipeline/start/stream",
          {
            body: JSON.stringify({
              article_id: article.id,
              auto_gate_one: autoGateOne,
            }),
          },
          {
            onEvent: async (event: PipelineEvent) => {
              if (
                event.event_type === "gate_pending" &&
                event.stage === "gate_two"
              ) {
                const content = await api.articles.getContent(article.id);
                if (content) setArticleContent(content);
              }
            },
          },
        );

        void refetch();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "알 수 없는 오류";
        setError(msg);
        setPipelineMode("idle");
      }
    },
    [
      setPipelineMode,
      setActiveArticle,
      addArticle,
      setError,
      setArticleContent,
      startStream,
      refetch,
    ],
  );

  const isRunning = usePipelineStore((s) => s.isRunning);
  const error = usePipelineStore((s) => s.error);

  return (
    <div
      className="app"
      data-sidebar={sidebarOpen ? "open" : "collapsed"}
      data-right={rightPanelOpen ? "shown" : "hidden"}
    >
      <Sidebar />
      <Topbar />

      <main className="main">
        {error && <div className="error-banner">{error}</div>}

        <Suspense>
          {activeArticle ? (
            <Editor article={activeArticle} />
          ) : (
            <Launcher onStart={handleStart} disabled={isRunning} />
          )}
        </Suspense>
      </main>

      <Suspense>
        <RightPanel />

        {gateModal && (
          <GateModal
            gate={gateModal.gate}
            runId={gateModal.runId}
            onClose={closeGateModal}
          />
        )}
      </Suspense>
    </div>
  );
}
