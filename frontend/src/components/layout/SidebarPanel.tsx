import { useEffect, useState } from "react";
import { useAppStore, type SidebarPanel as PanelType } from "../../stores/app-store";
import { api } from "../../api/client";
import { Icons } from "../common/Icons";
import type { PipelineRun } from "../../types/pipeline";

export function SidebarPanel() {
  const { sidebarPanel, setSidebarPanel } = useAppStore();
  if (!sidebarPanel) return null;

  return (
    <div className="sb-panel-overlay" onClick={() => setSidebarPanel(null)}>
      <div className="sb-panel" onClick={(e) => e.stopPropagation()}>
        <div className="sb-panel-header">
          <span className="sb-panel-title">{PANEL_TITLES[sidebarPanel]}</span>
          <button className="sb-panel-close" onClick={() => setSidebarPanel(null)}>
            <Icons.X s={14} />
          </button>
        </div>
        <div className="sb-panel-body">
          <PanelContent panel={sidebarPanel} />
        </div>
      </div>
    </div>
  );
}

const PANEL_TITLES: Record<NonNullable<PanelType>, string> = {
  pipelines: "파이프라인 실행 이력",
  "style-guide": "STYLE.md",
  tistory: "Tistory 연결",
  subagents: "Subagents",
  skills: "Skills",
  eval: "Eval Harness",
  mcp: "MCP & API",
};

function PanelContent({ panel }: { panel: NonNullable<PanelType> }) {
  switch (panel) {
    case "pipelines":
      return <PipelinesPanel />;
    case "style-guide":
      return <StyleGuidePanel />;
    case "tistory":
      return <TistoryPanel />;
    default:
      return <PlaceholderPanel name={PANEL_TITLES[panel]} />;
  }
}

function PipelinesPanel() {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.pipeline
      .listRuns(undefined, 50)
      .then((res) => {
        if (res.success && res.data) setRuns(res.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="sb-panel-loading">불러오는 중...</div>;
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const STATUS_LABELS: Record<string, string> = {
  running: "실행 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  paused: "일시정지",
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StyleGuidePanel() {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.settings
      .getStyleGuide()
      .then((text) => setContent(text))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="sb-panel-loading">불러오는 중...</div>;

  return <pre className="sb-panel-pre">{content ?? "파일을 찾을 수 없습니다."}</pre>;
}

function TistoryPanel() {
  return (
    <div className="sb-panel-info">
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">블로그</span>
        <span>jaylenhan.tistory.com</span>
      </div>
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">연결 방식</span>
        <span>Playwright (수동 로그인)</span>
      </div>
      <p className="sb-panel-note">
        Tistory 발행은 Gate 2 승인 후 Playwright가 브라우저를 열어 진행합니다.
        카카오 로그인이 필요할 경우 수동으로 진행해 주세요.
      </p>
    </div>
  );
}

function PlaceholderPanel({ name }: { name: string }) {
  return (
    <div className="sb-panel-placeholder">
      <Icons.Beaker s={32} w={1} />
      <p>{name}</p>
      <span>개발 예정</span>
    </div>
  );
}
