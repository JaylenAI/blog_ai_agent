import { useCallback, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import type { Article } from "../../types/article";
import { STATUS_DISPLAY } from "./shared";

export function DashboardPanel() {
  const articles = useAppStore((s) => s.articles);
  const setArticles = useAppStore((s) => s.setArticles);
  const setActiveArticle = useAppStore((s) => s.setActiveArticle);
  const setSidebarPanel = useAppStore((s) => s.setSidebarPanel);
  const addToast = useAppStore((s) => s.addToast);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "name">(
    "newest",
  );

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
      if (sortBy === "newest")
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      if (sortBy === "oldest")
        return (
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
      return (a.title ?? a.topic).localeCompare(b.title ?? b.topic);
    });

  const stats = {
    total: articles.length,
    published: articles.filter((a) => a.status === "published").length,
    draft: articles.filter((a) => a.status === "draft").length,
    totalWords: articles.reduce((s, a) => s + (a.word_count ?? 0), 0),
  };

  const handleStatusChange = useCallback(
    async (article: Article, newStatus: string) => {
      try {
        await api.articles.update(article.id, { status: newStatus });
        setArticles(
          articles.map((a) =>
            a.id === article.id
              ? { ...a, status: newStatus as Article["status"] }
              : a,
          ),
        );
        addToast({
          type: "success",
          message: `상태 변경: ${STATUS_DISPLAY[newStatus]?.label ?? newStatus}`,
        });
      } catch {
        addToast({ type: "error", message: "상태 변경 실패" });
      }
    },
    [articles, addToast, setArticles],
  );

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
          <div className="dash-stat-value">
            {stats.totalWords.toLocaleString()}
          </div>
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
                  <span>
                    {new Date(a.created_at).toLocaleDateString("ko-KR")}
                  </span>
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
          <div className="sb-panel-empty">
            조건에 맞는 아티클이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
