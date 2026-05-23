import { useCallback, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import type { SidebarPanel } from "../../stores/app-store";
import { useUIStore } from "../../stores/ui-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useNotificationStore } from "../../stores/notification-store";
import { ConfirmModal } from "../common/ConfirmModal";
import { Icons } from "../common/Icons";
import type { Article } from "../../types/article";

export function Sidebar({ className = "" }: { className?: string }) {
  const { articles, activeArticle, setActiveArticle, setSidebarPanel, setArticles, addToast } = useAppStore();
  const events = usePipelineStore((s) => s.events);
  const [openDrafts, setOpenDrafts] = useState(true);
  const [openPub, setOpenPub] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Article | null>(null);
  const [showNotifs, setShowNotifs] = useState(false);
  const notifications = useNotificationStore((s) => s.notifications);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  const openPanel = (panel: NonNullable<SidebarPanel>) => setSidebarPanel(panel);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      const res = await api.articles.delete(deleteTarget.id);
      if (res.success) {
        setArticles(articles.filter((a) => a.id !== deleteTarget.id));
        if (activeArticle?.id === deleteTarget.id) setActiveArticle(null);
        addToast({ type: "success", message: `"${deleteTarget.title ?? deleteTarget.topic}" 삭제 완료` });
      }
    } catch {
      addToast({ type: "error", message: "삭제 실패" });
    }
    setDeleteTarget(null);
  }, [deleteTarget, articles, activeArticle, setArticles, setActiveArticle, addToast]);

  const filtered = searchQuery.trim()
    ? articles.filter((a) => {
        const q = searchQuery.toLowerCase();
        return (
          a.topic.toLowerCase().includes(q) ||
          (a.title ?? "").toLowerCase().includes(q)
        );
      })
    : articles;

  const drafts = filtered.filter((a) => a.status !== "published");
  const published = filtered.filter((a) => a.status === "published");

  const referenceCount = events
    .filter(
      (e) =>
        e.event_type === "stage_complete" &&
        e.stage === "researcher" &&
        e.data?.librarian,
    )
    .reduce(
      (sum, e) =>
        sum + ((e.data?.reference_count as number | undefined) ?? 0),
      0,
    );

  return (
    <aside className={`sidebar ${className}`.trim()}>
      <div className="sidebar-brand">
        <div className="brand-mark">B</div>
        <div className="brand-name">Blog Agent</div>
        <div className="brand-meta">v0.4</div>
      </div>

      <div className="sidebar-scroll">
        <div className="sb-section">
          <div onClick={() => setShowSearch((v) => !v)}>
            <SbRow icon={<Icons.Search />} label="검색" />
          </div>
          {showSearch && (
            <input
              className="sb-search"
              type="text"
              placeholder="제목 또는 주제 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          )}
          <div onClick={() => { setShowNotifs((v) => !v); if (!showNotifs) markAllRead(); }}>
            <SbRow icon={<Icons.Inbox />} label="알림" count={unreadCount() > 0 ? unreadCount() : undefined} />
          </div>
          {showNotifs && (
            <div className="sb-notif-panel">
              {notifications.length === 0 ? (
                <div className="sb-notif-empty">알림이 없습니다</div>
              ) : (
                notifications.slice(0, 10).map((n) => (
                  <div
                    key={n.id}
                    className={`sb-notif-item ${n.read ? "" : "unread"} ${n.articleId || n.runId ? "clickable" : ""}`}
                    onClick={() => {
                      if (n.articleId) {
                        const target = articles.find((a) => a.id === n.articleId);
                        if (target) {
                          setActiveArticle(target);
                          setShowNotifs(false);
                        }
                      } else if (n.runId) {
                        setSidebarPanel("pipelines");
                        setShowNotifs(false);
                      }
                    }}
                  >
                    <div className="sb-notif-title">{n.title}</div>
                    <div className="sb-notif-msg">{n.message}</div>
                    <div className="sb-notif-time">{new Date(n.timestamp).toLocaleTimeString("ko-KR")}</div>
                  </div>
                ))
              )}
            </div>
          )}
          <div onClick={() => setActiveArticle(null)}>
            <SbRow icon={<Icons.Plus />} label="새 글 만들기" />
          </div>
        </div>

        <div className="sb-section">
          <div className="sb-section-title">Workspaces</div>
          <SbRow
            icon={<Icons.Folder />}
            label="AI의 정석 · jaylenhan"
            chev
            openChev
          />
          <SbRow
            indent={1}
            icon={<Icons.Doc />}
            label="Drafts"
            count={drafts.length}
            chev
            openChev={openDrafts}
            onClick={() => setOpenDrafts((v) => !v)}
          />
          {openDrafts &&
            drafts.map((d) => (
              <ArticleRow
                key={d.id}
                article={d}
                active={activeArticle?.id === d.id}
                onClick={() => setActiveArticle(d)}
                onDelete={() => setDeleteTarget(d)}
              />
            ))}
          <SbRow
            indent={1}
            icon={<Icons.Send />}
            label="Published"
            count={published.length}
            chev
            openChev={openPub}
            onClick={() => setOpenPub((v) => !v)}
          />
          {openPub &&
            published.map((p) => (
              <ArticleRow
                key={p.id}
                article={p}
                active={activeArticle?.id === p.id}
                onClick={() => setActiveArticle(p)}
                onDelete={() => setDeleteTarget(p)}
              />
            ))}
          <SbRow
            indent={1}
            icon={<Icons.Tag />}
            label="References"
            count={referenceCount > 0 ? referenceCount : undefined}
            onClick={() => {
              const store = useUIStore.getState();
              if (!store.rightPanelOpen) store.toggleRightPanel();
              store.setRightPanelTab("references");
            }}
          />
        </div>

        <div className="sb-section">
          <div className="sb-section-title">관리</div>
          <SbRow icon={<Icons.Layers />} label="대시보드" onClick={() => openPanel("dashboard")} />
        </div>

        <div className="sb-section">
          <div className="sb-section-title">Agent</div>
          <SbRow icon={<Icons.Layers />} label="Pipelines" onClick={() => openPanel("pipelines")} />
          <SbRow icon={<Icons.Bot />} label="Subagents" count={4} onClick={() => openPanel("subagents")} />
          <SbRow icon={<Icons.Sparkle />} label="Skills" count={6} onClick={() => openPanel("skills")} />
          <SbRow icon={<Icons.Beaker />} label="Eval Harness" onClick={() => openPanel("eval")} />
        </div>

        <div className="sb-section">
          <div className="sb-section-title">Settings</div>
          <SbRow icon={<Icons.Hash />} label="STYLE.md" onClick={() => openPanel("style-guide")} />
          <SbRow icon={<Icons.Globe />} label="Tistory 연결" onClick={() => openPanel("tistory")} />
          <SbRow icon={<Icons.Cog />} label="MCP & API" onClick={() => openPanel("mcp")} />
          <SbRow icon={<Icons.Cog />} label="종합 설정" onClick={() => openPanel("settings")} />
        </div>
      </div>

      {deleteTarget && (
        <ConfirmModal
          title="아티클 삭제"
          message={`"${deleteTarget.title ?? deleteTarget.topic}"을(를) 삭제하시겠습니까? 생성된 콘텐츠와 이미지가 모두 삭제됩니다.`}
          confirmLabel="삭제"
          variant="danger"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      <div className="sb-foot">
        <div className="avatar">JH</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="sb-foot-name">Jaylen H.</div>
          <div className="sb-foot-sub">jaylenhan.tistory.com</div>
        </div>
      </div>
    </aside>
  );
}

function SbRow({
  indent = 0,
  icon,
  label,
  count,
  dot,
  active,
  chev,
  openChev,
  onClick,
}: {
  indent?: number;
  icon?: React.ReactNode;
  label: string;
  count?: number;
  dot?: boolean;
  active?: boolean;
  chev?: boolean;
  openChev?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      className={`sb-row indent-${indent} ${active ? "active" : ""}`}
      onClick={onClick}
      {...(onClick ? {
        tabIndex: 0,
        role: "button" as const,
        onKeyDown: (e: React.KeyboardEvent) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onClick();
          }
        },
      } : {})}
    >
      {chev !== undefined && (
        <Icons.Chevron
          s={12}
          w={1.6}
          className={`chev ${openChev ? "open" : ""}`}
        />
      )}
      {icon && <span className="ico">{icon}</span>}
      {dot && <span className="dot" />}
      <span className="lbl">{label}</span>
      {count !== undefined && <span className="count">{count}</span>}
    </div>
  );
}

function ArticleRow({
  article,
  active,
  onClick,
  onDelete,
}: {
  article: Article;
  active: boolean;
  onClick: () => void;
  onDelete: () => void;
}) {
  const isGenerating =
    article.status === "generating" || article.status === "researching";

  return (
    <div className="article-row-wrap" onClick={onClick}>
      <SbRow
        indent={2}
        icon={<Icons.Doc />}
        label={article.title ?? article.topic}
        dot={isGenerating}
        active={active}
      />
      <button
        className="article-delete-btn"
        title="삭제"
        aria-label="삭제"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
      >
        <Icons.X s={10} w={2} />
      </button>
    </div>
  );
}
