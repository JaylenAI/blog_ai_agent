import { useCallback, useEffect, useState } from "react";
import { useAppStore, type SidebarPanel as PanelType } from "../../stores/app-store";
import { api } from "../../api/client";
import { Icons } from "../common/Icons";
import type { Article } from "../../types/article";
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
  dashboard: "블로그 대시보드",
  settings: "종합 설정",
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
    case "dashboard":
      return <DashboardPanel />;
    case "settings":
      return <SettingsPanel />;
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

const STATUS_DISPLAY: Record<string, { label: string; cls: string }> = {
  draft: { label: "초안", cls: "draft" },
  researching: { label: "자료수집", cls: "active" },
  outlining: { label: "아웃라인", cls: "active" },
  generating: { label: "생성 중", cls: "active" },
  validating: { label: "검증 중", cls: "active" },
  review: { label: "검수 대기", cls: "review" },
  published: { label: "발행 완료", cls: "done" },
  failed: { label: "실패", cls: "failed" },
};

function DashboardPanel() {
  const articles = useAppStore((s) => s.articles);
  const setActiveArticle = useAppStore((s) => s.setActiveArticle);
  const setSidebarPanel = useAppStore((s) => s.setSidebarPanel);
  const addToast = useAppStore((s) => s.addToast);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "name">("newest");

  const filtered = articles
    .filter((a) => {
      if (filterStatus !== "all" && a.status !== filterStatus) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          a.topic.toLowerCase().includes(q) ||
          (a.title ?? "").toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "newest") return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === "oldest") return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return (a.title ?? a.topic).localeCompare(b.title ?? b.topic);
    });

  const stats = {
    total: articles.length,
    published: articles.filter((a) => a.status === "published").length,
    draft: articles.filter((a) => a.status === "draft").length,
    totalWords: articles.reduce((s, a) => s + (a.word_count ?? 0), 0),
  };

  const handleStatusChange = useCallback(async (article: Article, newStatus: string) => {
    try {
      await api.articles.update(article.id, { status: newStatus });
      useAppStore.getState().setArticles(
        articles.map((a) => a.id === article.id ? { ...a, status: newStatus as Article["status"] } : a)
      );
      addToast({ type: "success", message: `상태 변경: ${STATUS_DISPLAY[newStatus]?.label ?? newStatus}` });
    } catch {
      addToast({ type: "error", message: "상태 변경 실패" });
    }
  }, [articles, addToast]);

  return (
    <div className="dashboard">
      <div className="dash-stats">
        <div className="dash-stat">
          <div className="dash-stat-value">{stats.total}</div>
          <div className="dash-stat-label">전체</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-value">{stats.published}</div>
          <div className="dash-stat-label">발행</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-value">{stats.draft}</div>
          <div className="dash-stat-label">초안</div>
        </div>
        <div className="dash-stat">
          <div className="dash-stat-value">{stats.totalWords.toLocaleString()}</div>
          <div className="dash-stat-label">총 글자수</div>
        </div>
      </div>

      <div className="dash-controls">
        <input
          className="dash-search"
          type="text"
          placeholder="검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="dash-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">전체 상태</option>
          <option value="draft">초안</option>
          <option value="published">발행 완료</option>
          <option value="failed">실패</option>
        </select>
        <select
          className="dash-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
        >
          <option value="newest">최신순</option>
          <option value="oldest">오래된순</option>
          <option value="name">이름순</option>
        </select>
      </div>

      <div className="dash-list">
        {filtered.map((a) => {
          const sd = STATUS_DISPLAY[a.status] ?? { label: a.status, cls: "" };
          return (
            <div key={a.id} className="dash-item">
              <div
                className="dash-item-main"
                onClick={() => {
                  setActiveArticle(a);
                  setSidebarPanel(null);
                }}
              >
                <div className="dash-item-title">{a.title ?? a.topic}</div>
                <div className="dash-item-meta">
                  <span className={`dash-status ${sd.cls}`}>{sd.label}</span>
                  <span>{a.word_count?.toLocaleString() ?? 0}자</span>
                  <span>{new Date(a.created_at).toLocaleDateString("ko-KR")}</span>
                </div>
              </div>
              <select
                className="dash-status-select"
                value={a.status}
                onChange={(e) => handleStatusChange(a, e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="draft">초안</option>
                <option value="review">검수 대기</option>
                <option value="published">발행 완료</option>
              </select>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="sb-panel-empty">조건에 맞는 아티클이 없습니다.</div>
        )}
      </div>
    </div>
  );
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

interface ObsidianSettings {
  vault_path: string;
  frontmatter_tags: string[];
  auto_save: boolean;
}

interface GeneralSettings {
  tistory_blog_url: string;
  stage_timeout: number;
  image_generation_enabled: boolean;
  max_images_per_article: number;
  log_level: string;
}

function SettingsPanel() {
  const addToast = useAppStore((s) => s.addToast);
  const [tab, setTab] = useState<"obsidian" | "general" | "batch">("obsidian");
  const [obsidian, setObsidian] = useState<ObsidianSettings | null>(null);
  const [general, setGeneral] = useState<GeneralSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings.getObsidian().then((res) => {
      if (res.success && res.data) setObsidian(res.data as ObsidianSettings);
    });
    api.settings.getGeneral().then((res) => {
      if (res.success && res.data) setGeneral(res.data as GeneralSettings);
    });
  }, []);

  const saveObsidian = useCallback(async () => {
    if (!obsidian) return;
    setSaving(true);
    try {
      await api.settings.updateObsidian(obsidian);
      addToast({ type: "success", message: "Obsidian 설정 저장 완료" });
    } catch {
      addToast({ type: "error", message: "저장 실패" });
    } finally {
      setSaving(false);
    }
  }, [obsidian, addToast]);

  const saveGeneral = useCallback(async () => {
    if (!general) return;
    setSaving(true);
    try {
      await api.settings.updateGeneral(general);
      addToast({ type: "success", message: "일반 설정 저장 완료" });
    } catch {
      addToast({ type: "error", message: "저장 실패" });
    } finally {
      setSaving(false);
    }
  }, [general, addToast]);

  return (
    <div className="settings-panel">
      <div className="settings-tabs">
        <button
          className={`settings-tab ${tab === "obsidian" ? "active" : ""}`}
          onClick={() => setTab("obsidian")}
        >
          Obsidian
        </button>
        <button
          className={`settings-tab ${tab === "general" ? "active" : ""}`}
          onClick={() => setTab("general")}
        >
          일반
        </button>
        <button
          className={`settings-tab ${tab === "batch" ? "active" : ""}`}
          onClick={() => setTab("batch")}
        >
          일괄 편집
        </button>
      </div>

      {tab === "obsidian" && obsidian && (
        <div className="settings-form">
          <div className="settings-group">
            <label className="settings-label">Obsidian Vault 경로</label>
            <input
              className="settings-input"
              type="text"
              value={obsidian.vault_path}
              onChange={(e) => setObsidian({ ...obsidian, vault_path: e.target.value })}
              placeholder="/Users/name/ObsidianVault"
            />
            <span className="settings-hint">Obsidian 볼트의 절대 경로를 입력하세요</span>
          </div>

          <div className="settings-group">
            <label className="settings-label">프론트매터 기본 태그</label>
            <input
              className="settings-input"
              type="text"
              value={obsidian.frontmatter_tags.join(", ")}
              onChange={(e) =>
                setObsidian({
                  ...obsidian,
                  frontmatter_tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean),
                })
              }
              placeholder="blog/published, category/ai"
            />
            <span className="settings-hint">쉼표로 구분하여 입력</span>
          </div>

          <div className="settings-group">
            <label className="settings-label">
              <input
                type="checkbox"
                checked={obsidian.auto_save}
                onChange={(e) => setObsidian({ ...obsidian, auto_save: e.target.checked })}
              />
              {" "}발행 시 자동 저장
            </label>
            <span className="settings-hint">Gate 2 통과 후 자동으로 Obsidian에 저장</span>
          </div>

          <button className="settings-save" onClick={saveObsidian} disabled={saving}>
            {saving ? "저장 중..." : "Obsidian 설정 저장"}
          </button>
        </div>
      )}

      {tab === "general" && general && (
        <div className="settings-form">
          <div className="settings-group">
            <label className="settings-label">Tistory 블로그 URL</label>
            <input
              className="settings-input"
              type="text"
              value={general.tistory_blog_url}
              onChange={(e) => setGeneral({ ...general, tistory_blog_url: e.target.value })}
              placeholder="https://jaylenhan.tistory.com"
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">스테이지 타임아웃 (초)</label>
            <input
              className="settings-input"
              type="number"
              value={general.stage_timeout}
              onChange={(e) => setGeneral({ ...general, stage_timeout: Number(e.target.value) })}
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">
              <input
                type="checkbox"
                checked={general.image_generation_enabled}
                onChange={(e) => setGeneral({ ...general, image_generation_enabled: e.target.checked })}
              />
              {" "}이미지 자동 생성
            </label>
          </div>

          <div className="settings-group">
            <label className="settings-label">글당 최대 이미지 수</label>
            <input
              className="settings-input"
              type="number"
              value={general.max_images_per_article}
              onChange={(e) => setGeneral({ ...general, max_images_per_article: Number(e.target.value) })}
              min={0}
              max={10}
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">로그 레벨</label>
            <select
              className="settings-input"
              value={general.log_level}
              onChange={(e) => setGeneral({ ...general, log_level: e.target.value })}
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>

          <button className="settings-save" onClick={saveGeneral} disabled={saving}>
            {saving ? "저장 중..." : "일반 설정 저장"}
          </button>
        </div>
      )}

      {tab === "batch" && <BatchEditPanel />}
    </div>
  );
}

function BatchEditPanel() {
  const articles = useAppStore((s) => s.articles);
  const addToast = useAppStore((s) => s.addToast);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [category, setCategory] = useState("");
  const [tags, setTags] = useState("");
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const toggleAll = () => {
    if (selected.size === articles.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(articles.map((a) => a.id)));
    }
  };

  const handleApply = async () => {
    if (selected.size === 0) return;
    setSaving(true);
    try {
      const data: { article_ids: number[]; category?: string; tags?: string[]; status?: string } = {
        article_ids: [...selected],
      };
      if (category) data.category = category;
      if (tags) data.tags = tags.split(",").map((t) => t.trim()).filter(Boolean);
      if (status) data.status = status;

      const res = await api.settings.batchUpdate(data);
      if (res.success) {
        addToast({ type: "success", message: `${res.data?.updated ?? 0}개 아티클 업데이트 완료` });
        setSelected(new Set());
      }
    } catch {
      addToast({ type: "error", message: "일괄 업데이트 실패" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-form">
      <div className="batch-select-header">
        <label>
          <input
            type="checkbox"
            checked={selected.size === articles.length && articles.length > 0}
            onChange={toggleAll}
          />
          {" "}전체 선택 ({selected.size}/{articles.length})
        </label>
      </div>

      <div className="batch-list">
        {articles.map((a) => (
          <label key={a.id} className="batch-item">
            <input
              type="checkbox"
              checked={selected.has(a.id)}
              onChange={() => toggleSelect(a.id)}
            />
            <span className="batch-item-title">{a.title ?? a.topic}</span>
          </label>
        ))}
      </div>

      {selected.size > 0 && (
        <div className="batch-fields">
          <div className="settings-group">
            <label className="settings-label">카테고리 변경</label>
            <input
              className="settings-input"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="새 카테고리 (비우면 변경 안 함)"
            />
          </div>
          <div className="settings-group">
            <label className="settings-label">태그 변경</label>
            <input
              className="settings-input"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="태그1, 태그2 (비우면 변경 안 함)"
            />
          </div>
          <div className="settings-group">
            <label className="settings-label">상태 변경</label>
            <select
              className="settings-input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">변경 안 함</option>
              <option value="draft">초안</option>
              <option value="review">검수 대기</option>
              <option value="published">발행 완료</option>
            </select>
          </div>
          <button className="settings-save" onClick={handleApply} disabled={saving}>
            {saving ? "적용 중..." : `${selected.size}개 아티클에 적용`}
          </button>
        </div>
      )}
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
