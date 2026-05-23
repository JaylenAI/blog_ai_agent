import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { Icons } from "../common/Icons";
import {
  PipelineTab,
  ReferencesTab,
  ValidationTab,
  HistoryTab,
} from "../tabs";

export function RightPanel({
  className = "",
}: { className?: string } = {}) {
  const { rightPanelTab, setRightPanelTab, pipelineMode } =
    useAppStore();

  useEffect(() => {
    if (pipelineMode === "validate" || pipelineMode === "gate2") {
      setRightPanelTab("validation");
    } else if (pipelineMode === "research") {
      setRightPanelTab("pipeline");
    }
  }, [pipelineMode, setRightPanelTab]);

  return (
    <aside className={`right-panel ${className}`.trim()}>
      <div className="rp-tabs">
        <button
          className={`rp-tab ${rightPanelTab === "pipeline" ? "active" : ""}`}
          onClick={() => setRightPanelTab("pipeline")}
        >
          <Icons.Layers s={13} /> 파이프라인
        </button>
        <button
          className={`rp-tab ${rightPanelTab === "references" ? "active" : ""}`}
          onClick={() => setRightPanelTab("references")}
        >
          <Icons.Tag s={13} /> 자료
        </button>
        <button
          className={`rp-tab ${rightPanelTab === "validation" ? "active" : ""}`}
          onClick={() => setRightPanelTab("validation")}
        >
          <Icons.CheckCircle s={13} /> 검증
        </button>
        <button
          className={`rp-tab ${rightPanelTab === "history" ? "active" : ""}`}
          onClick={() => setRightPanelTab("history")}
        >
          <Icons.Layers s={13} /> 히스토리
        </button>
      </div>
      <div className="rp-body">
        {rightPanelTab === "pipeline" && <PipelineTab />}
        {rightPanelTab === "references" && <ReferencesTab />}
        {rightPanelTab === "validation" && <ValidationTab />}
        {rightPanelTab === "history" && <HistoryTab />}
      </div>
    </aside>
  );
}
