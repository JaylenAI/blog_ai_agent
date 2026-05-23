import { useCallback, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { usePipelineSSE } from "../../hooks/use-pipeline-sse";
import { Icons } from "../common/Icons";

const STAGE_LABELS: Record<
  string,
  { txt: string; cls: string }
> = {
  idle: { txt: "준비", cls: "" },
  research: { txt: "Researcher · 자료수집 중", cls: "live" },
  outline: { txt: "Gate 1 · 아웃라인 대기", cls: "live" },
  generate: { txt: "Generator · 본문 생성 중", cls: "live" },
  validate: { txt: "Validator · 14항목 검증", cls: "live" },
  gate2: { txt: "Gate 2 · 최종 검수", cls: "live" },
  published: { txt: "Tistory 발행 완료", cls: "done" },
};

export function Topbar({
  hamburger = false,
  onHamburgerClick,
}: {
  hamburger?: boolean;
  onHamburgerClick?: () => void;
} = {}) {
  const {
    toggleSidebar,
    toggleRightPanel,
    activeArticle,
    pipelineMode,
    openGateModal,
    gateModal,
    theme,
    setTheme,
    setPublishKitOpen,
    setPipelineMode,
    addToast,
    setArticleContent,
  } = useAppStore();

  const currentRun = usePipelineStore((s) => s.currentRun);
  const pipelineError = usePipelineStore((s) => s.error);
  const { startStream } = usePipelineSSE();
  const [retrying, setRetrying] = useState(false);

  const stage = STAGE_LABELS[pipelineMode] ?? { txt: "준비", cls: "" };
  const isGateMode = pipelineMode === "outline" || pipelineMode === "gate2";
  const runId = useAppStore((s) => {
    const ev = s.articles.find((a) => a.id === s.activeArticle?.id);
    return ev?.id ?? 0;
  });

  const isFailed = currentRun?.status === "failed" || !!pipelineError;
  const isRunning = pipelineMode !== "idle" && pipelineMode !== "published";

  const handleCancel = useCallback(async () => {
    if (!currentRun) return;
    try {
      await api.pipeline.cancel(currentRun.id);
      setPipelineMode("idle");
      usePipelineStore.getState().reset();
      addToast({ type: "info", message: "파이프라인 취소됨" });
    } catch {
      addToast({ type: "error", message: "취소 실패" });
    }
  }, [currentRun, setPipelineMode, addToast]);

  const handleRetry = useCallback(async () => {
    if (!currentRun || !activeArticle) return;
    setRetrying(true);
    try {
      setPipelineMode("research");
      usePipelineStore.getState().reset();
      await startStream(
        `/pipeline/runs/${currentRun.id}/retry/stream`,
        {},
        {
          onEvent: async (event) => {
            if (
              event.event_type === "gate_pending" &&
              event.stage === "gate_two"
            ) {
              const content = await api.articles.getContent(activeArticle.id);
              if (content) setArticleContent(content);
            }
          },
        },
      );
    } catch {
      addToast({ type: "error", message: "재시도 실패" });
    } finally {
      setRetrying(false);
    }
  }, [currentRun, activeArticle, setPipelineMode, startStream, setArticleContent, addToast]);

  const handleRevalidate = useCallback(async () => {
    if (!activeArticle) return;
    try {
      setPipelineMode("validate");
      usePipelineStore.getState().reset();
      await startStream(
        "/pipeline/validate-only/stream",
        { body: JSON.stringify({ article_id: activeArticle.id }) },
        {},
      );
      addToast({ type: "success", message: "재검증 완료" });
    } catch {
      addToast({ type: "error", message: "재검증 실패" });
    } finally {
      setPipelineMode("idle");
    }
  }, [activeArticle, setPipelineMode, startStream, addToast]);

  const handleSaveObsidian = useCallback(async () => {
    if (!activeArticle) return;
    try {
      const res = await api.articles.saveObsidian(activeArticle.id);
      if (res.success) {
        addToast({ type: "success", message: "Obsidian 저장 완료" });
      } else {
        addToast({ type: "error", message: res.error ?? "Obsidian 저장 실패" });
      }
    } catch {
      addToast({ type: "error", message: "Obsidian 저장 실패 — vault 경로를 확인해 주세요" });
    }
  }, [activeArticle, addToast]);

  const articleContent = useAppStore((s) => s.articleContent);
  const hasContent = !!articleContent;

  return (
    <header className="topbar">
      {hamburger ? (
        <button className="icon-btn hamburger-btn" title="메뉴" aria-label="메뉴 열기" onClick={onHamburgerClick}>
          <Icons.Menu />
        </button>
      ) : (
        <button className="icon-btn" title="사이드바" aria-label="사이드바 토글" onClick={toggleSidebar}>
          <Icons.Sidebar />
        </button>
      )}
      <div className="crumbs">
        <span className="crumb">AI의 정석</span>
        <span className="sep">/</span>
        <span className="crumb">Drafts</span>
        <span className="sep">/</span>
        <span className="crumb last">
          {activeArticle
            ? (activeArticle.title ?? activeArticle.topic)
            : "새 글"}
        </span>
      </div>

      <div className="topbar-right">
        {pipelineMode !== "idle" && (
          <button
            className={`pipeline-pill ${stage.cls}`}
            onClick={() => {
              if (isGateMode && gateModal === null) {
                openGateModal(
                  pipelineMode === "outline" ? "gate_one" : "gate_two",
                  runId,
                );
              }
            }}
            title={isGateMode ? "검수 모달 열기" : ""}
          >
            {stage.cls === "live" && <span className="pulse" />}
            {stage.txt}
          </button>
        )}
        {isFailed && currentRun && (
          <button
            className="icon-btn retry-btn"
            onClick={handleRetry}
            disabled={retrying}
          >
            <Icons.Sparkle s={13} />
            {retrying ? "재시도 중..." : "재시도"}
          </button>
        )}
        {isRunning && currentRun && (
          <button className="icon-btn cancel-btn" onClick={handleCancel}>
            <Icons.X s={13} /> 취소
          </button>
        )}
        {hasContent && activeArticle && pipelineMode === "idle" && (
          <>
            <button className="icon-btn" title="재검증" onClick={handleRevalidate}>
              <Icons.CheckCircle s={13} /> 재검증
            </button>
            <button className="icon-btn" title="Obsidian 저장" onClick={handleSaveObsidian}>
              <Icons.Doc s={13} /> Obsidian
            </button>
          </>
        )}
        <button
          className="icon-btn"
          title="발행 준비"
          disabled={!activeArticle}
          onClick={() => setPublishKitOpen(true)}
        >
          <Icons.Send s={14} /> 발행 준비
        </button>
        <button
          className="icon-btn ghost"
          title={theme === "light" ? "다크 모드" : "라이트 모드"}
          aria-label="테마 전환"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
        >
          {theme === "light" ? <Icons.Moon s={14} /> : <Icons.Sun s={14} />}
        </button>
        <button className="icon-btn primary" aria-label="파이프라인 패널" onClick={toggleRightPanel}>
          파이프라인
        </button>
      </div>
    </header>
  );
}
