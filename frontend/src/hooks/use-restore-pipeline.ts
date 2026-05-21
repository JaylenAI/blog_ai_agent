import { useEffect, useRef } from "react";
import { api } from "../api/client";
import { useAppStore } from "../stores/app-store";
import { usePipelineStore } from "../stores/pipeline-store";
import type { PipelineMode } from "../types/pipeline";

const STAGE_TO_MODE: Record<string, PipelineMode> = {
  router: "research",
  researcher: "research",
  outliner: "outline",
  gate_one: "outline",
  generator: "generate",
  validator: "validate",
  gate_two: "gate2",
  publisher: "published",
};

export function useRestorePipeline() {
  const didRestore = useRef(false);
  const { setPipelineMode, setActiveArticle, openGateModal, setArticleContent } =
    useAppStore();
  const { setRunning } = usePipelineStore();

  useEffect(() => {
    if (didRestore.current) return;
    didRestore.current = true;

    async function restore() {
      try {
        const res = await api.pipeline.getActiveRun();
        if (!res.success || !res.data) return;

        const run = res.data;
        const mode = STAGE_TO_MODE[run.current_stage] ?? "idle";
        setPipelineMode(mode);

        const articleRes = await api.articles.get(run.article_id);
        if (articleRes.success && articleRes.data) {
          setActiveArticle(articleRes.data);
        }

        if (run.status === "paused") {
          const gate =
            run.current_stage === "gate_one" ? "gate_one" : "gate_two";
          openGateModal(gate, run.id);

          if (gate === "gate_two" && articleRes.data) {
            const content = await api.articles.getContent(articleRes.data.id);
            if (content) setArticleContent(content);
          }
        } else if (run.status === "running") {
          setRunning(true);
        }
      } catch {
        // 복원 실패는 치명적이지 않음
      }
    }

    void restore();
  }, [
    setPipelineMode,
    setActiveArticle,
    openGateModal,
    setArticleContent,
    setRunning,
  ]);
}
