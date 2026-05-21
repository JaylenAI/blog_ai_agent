import { useAppStore } from "../../stores/app-store";
import type { Article } from "../../types/article";

const DRAFT_STATUSES = new Set([
  "draft",
  "researching",
  "outlining",
  "generating",
  "validating",
  "review",
  "publishing",
  "failed",
]);

function groupArticles(articles: Article[]) {
  const drafts: Article[] = [];
  const published: Article[] = [];
  for (const a of articles) {
    if (a.status === "published") {
      published.push(a);
    } else if (DRAFT_STATUSES.has(a.status)) {
      drafts.push(a);
    }
  }
  return { drafts, published };
}

export function Sidebar() {
  const { articles, activeArticle, setActiveArticle, articlesLoading } =
    useAppStore();
  const { drafts, published } = groupArticles(articles);

  return (
    <aside
      className="flex flex-col border-r h-full overflow-y-auto"
      style={{
        width: "var(--sidebar-w)",
        minWidth: "var(--sidebar-w)",
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-bg-sub)",
      }}
    >
      {/* Brand */}
      <div
        className="flex items-center gap-2 px-4 font-semibold"
        style={{ height: "var(--top-h)" }}
      >
        <span
          className="inline-flex items-center justify-center rounded-full text-white text-xs font-bold"
          style={{
            width: 22,
            height: 22,
            backgroundColor: "var(--color-accent)",
          }}
        >
          B
        </span>
        <span>Blog Agent</span>
        <span
          className="text-xs"
          style={{ color: "var(--color-text-faint)" }}
        >
          v0.1
        </span>
      </div>

      {/* New article button */}
      <div className="px-3 py-2">
        <button
          className="w-full text-left text-sm px-3 py-1.5 rounded-md transition-colors"
          style={{
            backgroundColor: "var(--color-bg-hover)",
            color: "var(--color-text)",
          }}
          onClick={() => setActiveArticle(null)}
        >
          + 새 글 만들기
        </button>
      </div>

      {/* Loading state */}
      {articlesLoading && articles.length === 0 && (
        <div className="px-3 space-y-2 py-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-7 rounded-md animate-pulse"
              style={{ backgroundColor: "var(--color-bg-hover)" }}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!articlesLoading && articles.length === 0 && (
        <div
          className="px-4 py-6 text-center text-xs"
          style={{ color: "var(--color-text-faint)" }}
        >
          아직 작성한 글이 없습니다
        </div>
      )}

      {/* Drafts */}
      {drafts.length > 0 && (
        <>
          <SectionHeader label="Drafts" count={drafts.length} />
          <nav className="px-2 space-y-0.5">
            {drafts.map((a) => (
              <ArticleItem
                key={a.id}
                article={a}
                active={activeArticle?.id === a.id}
                onClick={() => setActiveArticle(a)}
              />
            ))}
          </nav>
        </>
      )}

      {/* Published */}
      {published.length > 0 && (
        <>
          <SectionHeader label="Published" count={published.length} />
          <nav className="px-2 space-y-0.5">
            {published.map((a) => (
              <ArticleItem
                key={a.id}
                article={a}
                active={activeArticle?.id === a.id}
                onClick={() => setActiveArticle(a)}
              />
            ))}
          </nav>
        </>
      )}

      {/* Bottom user area */}
      <div
        className="mt-auto border-t px-4 py-3"
        style={{ borderColor: "var(--color-border)" }}
      >
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center justify-center rounded-full text-xs font-bold"
            style={{
              width: 24,
              height: 24,
              backgroundColor: "var(--color-bg-active)",
              color: "var(--color-text-muted)",
            }}
          >
            JH
          </span>
          <div
            className="text-xs"
            style={{ color: "var(--color-text-muted)" }}
          >
            <div>Jaylen H.</div>
            <div style={{ color: "var(--color-text-faint)" }}>
              jaylenhan.tistory.com
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function SectionHeader({ label, count }: { label: string; count: number }) {
  return (
    <div
      className="px-4 pt-4 pb-1 text-xs font-medium uppercase tracking-wider"
      style={{ color: "var(--color-text-faint)" }}
    >
      {label} ({count})
    </div>
  );
}

function ArticleItem({
  article,
  active,
  onClick,
}: {
  article: Article;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="w-full text-left text-sm px-3 py-1.5 rounded-md truncate transition-colors"
      style={{
        backgroundColor: active ? "var(--color-bg-active)" : "transparent",
        color: active ? "var(--color-text)" : "var(--color-text-muted)",
      }}
      onClick={onClick}
    >
      {article.title ?? article.topic}
    </button>
  );
}
