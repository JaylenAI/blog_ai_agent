import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useArticles } from "../../hooks/use-articles";
import { usePipelineSSE } from "../../hooks/use-pipeline-sse";
import { useRestorePipeline } from "../../hooks/use-restore-pipeline";
import { useIsMobile, useIsTablet } from "../../hooks/use-media-query";
import { api } from "../../api/client";
import { Sidebar } from "./Sidebar";
import { SidebarPanel } from "./SidebarPanel";
import { Topbar } from "./Topbar";
import { Launcher } from "../editor/Launcher";
import { ToastContainer } from "../common/ToastContainer";
import { LoadingSpinner } from "../common/LoadingSpinner";
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
const PublishKitModal = lazy(() =>
  import("../publish/PublishKitModal").then((m) => ({
    default: m.PublishKitModal,
  })),
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
    addToast,
  } = useAppStore();

  const theme = useAppStore((s) => s.theme);
  const density = useAppStore((s) => s.density);
  const accentHue = useAppStore((s) => s.accentHue);
  const publishKitOpen = useAppStore((s) => s.publishKitOpen);
  const setPublishKitOpen = useAppStore((s) => s.setPublishKitOpen);

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

  const [contentLoading, setContentLoading] = useState(false);
  const contentFetchId = useRef(0);

  useEffect(() => {
    if (!activeArticle) return;
    const fetchId = ++contentFetchId.current;
    setContentLoading(true);
    api.articles
      .getContent(activeArticle.id)
      .then((content) => {
        if (fetchId !== contentFetchId.current) return;
        setArticleContent(content);
      })
      .catch(() => {
        if (fetchId !== contentFetchId.current) return;
      })
      .finally(() => {
        if (fetchId === contentFetchId.current) setContentLoading(false);
      });
  }, [activeArticle, setArticleContent]);

  const handleStart = useCallback(
    async (topic: string, autoGateOne: boolean, formatId: string, length: "standard" | "long" = "standard") => {
      setPipelineMode("research");

      try {
        const createRes = await api.articles.create(topic, undefined, formatId);
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
              format_id: formatId,
              length,
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
        addToast({ type: "error", message: `글 생성 실패: ${msg}` });
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
      addToast,
    ],
  );

  const isRunning = usePipelineStore((s) => s.isRunning);
  const error = usePipelineStore((s) => s.error);

  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isMobile) setMobileSidebarOpen(false);
  }, [isMobile]);

  return (
    <div
      className="app"
      data-sidebar={sidebarOpen ? "open" : "collapsed"}
      data-right={rightPanelOpen ? "shown" : "hidden"}
    >
      <Sidebar className={mobileSidebarOpen ? "open" : ""} />
      {isMobile && mobileSidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}
      <Topbar
        hamburger={isMobile}
        onHamburgerClick={() => setMobileSidebarOpen((v) => !v)}
      />

      <main className="main">
        {error && <div className="error-banner">{error.length > 200 ? `${error.slice(0, 200)}…` : error}</div>}

        <Suspense>
          {activeArticle ? (
            contentLoading ? (
              <LoadingSpinner message="콘텐츠 불러오는 중..." />
            ) : (
              <Editor article={activeArticle} />
            )
          ) : (
            <Launcher onStart={handleStart} disabled={isRunning} />
          )}
        </Suspense>
      </main>

      <Suspense>
        <RightPanel className={isTablet && rightPanelOpen ? "open" : ""} />

        {gateModal && (
          <GateModal
            gate={gateModal.gate}
            runId={gateModal.runId}
            onClose={closeGateModal}
          />
        )}
      </Suspense>

      <SidebarPanel />

      <Suspense>
        {activeArticle && publishKitOpen && (
          <PublishKitModal
            articleId={activeArticle.id}
            onClose={() => setPublishKitOpen(false)}
          />
        )}
      </Suspense>

      <ToastContainer />
    </div>
  );
}
