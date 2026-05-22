import { useState } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { Icons } from "../common/Icons";
import type { Article } from "../../types/article";

export function Sidebar() {
  const { articles, activeArticle, setActiveArticle } = useAppStore();
  const events = usePipelineStore((s) => s.events);
  const [openDrafts, setOpenDrafts] = useState(true);
  const [openPub, setOpenPub] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

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
    <aside className="sidebar">
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
          <SbRow icon={<Icons.Inbox />} label="알림" />
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
              />
            ))}
          <SbRow
            indent={1}
            icon={<Icons.Tag />}
            label="References"
            count={referenceCount > 0 ? referenceCount : undefined}
          />
        </div>

        <div className="sb-section">
          <div className="sb-section-title">Agent</div>
          <SbRow icon={<Icons.Layers />} label="Pipelines" />
          <SbRow icon={<Icons.Bot />} label="Subagents" count={4} />
          <SbRow icon={<Icons.Sparkle />} label="Skills" count={6} />
          <SbRow icon={<Icons.Beaker />} label="Eval Harness" />
        </div>

        <div className="sb-section">
          <div className="sb-section-title">Settings</div>
          <SbRow icon={<Icons.Hash />} label="STYLE.md" />
          <SbRow icon={<Icons.Globe />} label="Tistory 연결" />
          <SbRow icon={<Icons.Cog />} label="MCP & API" />
        </div>
      </div>

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
}: {
  article: Article;
  active: boolean;
  onClick: () => void;
}) {
  const isGenerating =
    article.status === "generating" || article.status === "researching";

  return (
    <div onClick={onClick}>
      <SbRow
        indent={2}
        icon={<Icons.Doc />}
        label={article.title ?? article.topic}
        dot={isGenerating}
        active={active}
      />
    </div>
  );
}
